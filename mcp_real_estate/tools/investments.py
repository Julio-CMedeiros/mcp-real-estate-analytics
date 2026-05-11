"""Investment tools - rental yield estimation and investment scoring."""

from ..database import get_connection
from ..tool_groups import ToolGroup
from .registry import make_tool_registrar


TOOLS = {}
_register = make_tool_registrar(ToolGroup.INVESTMENTS, TOOLS)


# Average monthly rent per m² by neighborhood tier (simplified model)
_RENT_PER_M2 = {
    "premium": 22.0,   # Chiado, Príncipe Real
    "mid": 16.0,       # Parque das Nações, Cascais
    "affordable": 11.0, # Almada
}

_NEIGHBORHOOD_TIER = {
    1: "premium",   # Chiado
    2: "mid",       # Alfama
    3: "premium",   # Príncipe Real
    4: "mid",       # Parque das Nações
    5: "mid",       # Cascais
    6: "affordable", # Almada
}


@_register(
    name="estimate_rental_yield",
    description="Estimate gross and net rental yield for a property based on area, price, and neighborhood rental averages.",
    input_schema={
        "type": "object",
        "properties": {
            "property_id": {"type": "integer", "description": "Property to analyze"},
            "monthly_costs": {
                "type": "number",
                "description": "Estimated monthly ownership costs (condo + tax + maintenance). Default: 150€",
                "default": 150,
            },
        },
        "required": ["property_id"],
    },
)
def estimate_rental_yield(property_id: int, monthly_costs: float = 150) -> dict:
    conn = get_connection()
    prop = conn.execute(
        "SELECT p.*, n.name as neighborhood_name "
        "FROM properties p "
        "JOIN neighborhoods n ON p.neighborhood_id = n.id "
        "WHERE p.id = ?",
        [property_id],
    ).fetchone()

    if not prop:
        return {"error": "Property not found"}

    tier = _NEIGHBORHOOD_TIER.get(prop["neighborhood_id"], "mid")
    rent_m2 = _RENT_PER_M2[tier]
    monthly_rent = round(prop["area_m2"] * rent_m2, 2)
    annual_rent = monthly_rent * 12
    annual_costs = monthly_costs * 12

    gross_yield = (annual_rent / prop["price"]) * 100
    net_yield = ((annual_rent - annual_costs) / prop["price"]) * 100

    return {
        "property": {
            "id": prop["id"],
            "title": prop["title"],
            "neighborhood": prop["neighborhood_name"],
            "price": prop["price"],
            "area_m2": prop["area_m2"],
        },
        "rental_estimate": {
            "monthly_rent": monthly_rent,
            "annual_rent": annual_rent,
            "rent_per_m2": rent_m2,
            "tier": tier,
        },
        "yield": {
            "gross_pct": round(gross_yield, 2),
            "net_pct": round(net_yield, 2),
            "annual_costs": annual_costs,
        },
    }


@_register(
    name="get_investment_score",
    description="Calculate a composite investment score (0-100) based on rental yield, price appreciation trend, demand (days on market), and neighborhood quality.",
    input_schema={
        "type": "object",
        "properties": {
            "property_id": {"type": "integer", "description": "Property to score"},
        },
        "required": ["property_id"],
    },
)
def get_investment_score(property_id: int) -> dict:
    conn = get_connection()
    prop = conn.execute(
        "SELECT p.*, n.name as neighborhood_name, n.safety_score, n.transport_score, n.walkability_score "
        "FROM properties p "
        "JOIN neighborhoods n ON p.neighborhood_id = n.id "
        "WHERE p.id = ?",
        [property_id],
    ).fetchone()

    if not prop:
        return {"error": "Property not found"}

    # Component 1: Yield score (0-30)
    tier = _NEIGHBORHOOD_TIER.get(prop["neighborhood_id"], "mid")
    rent_m2 = _RENT_PER_M2[tier]
    gross_yield = (prop["area_m2"] * rent_m2 * 12 / prop["price"]) * 100
    yield_score = min(30, gross_yield * 5)  # 6%+ yield = max score

    # Component 2: Appreciation trend (0-25)
    trends = conn.execute(
        "SELECT avg_price_m2 FROM market_snapshots "
        "WHERE neighborhood_id = ? ORDER BY month DESC LIMIT 6",
        [prop["neighborhood_id"]],
    ).fetchall()
    if len(trends) >= 2:
        latest = trends[0]["avg_price_m2"]
        oldest = trends[-1]["avg_price_m2"]
        appreciation = ((latest - oldest) / oldest) * 100
        appreciation_score = min(25, appreciation * 3)
    else:
        appreciation_score = 12.5  # neutral

    # Component 3: Demand / liquidity (0-25)
    market = conn.execute(
        "SELECT avg_days_on_market FROM market_snapshots "
        "WHERE neighborhood_id = ? ORDER BY month DESC LIMIT 1",
        [prop["neighborhood_id"]],
    ).fetchone()
    if market:
        dom = market["avg_days_on_market"]
        demand_score = max(0, min(25, 25 - (dom - 30) * 0.5))  # <30 days = max
    else:
        demand_score = 12.5

    # Component 4: Location quality (0-20)
    location_score = (
        (prop["safety_score"] + prop["transport_score"] + prop["walkability_score"]) / 30
    ) * 20

    total = round(yield_score + appreciation_score + demand_score + location_score, 1)

    return {
        "property": {
            "id": prop["id"],
            "title": prop["title"],
            "neighborhood": prop["neighborhood_name"],
        },
        "investment_score": min(100, total),
        "components": {
            "yield": {"score": round(yield_score, 1), "max": 30, "gross_yield_pct": round(gross_yield, 2)},
            "appreciation": {"score": round(appreciation_score, 1), "max": 25},
            "demand": {"score": round(demand_score, 1), "max": 25},
            "location_quality": {"score": round(location_score, 1), "max": 20},
        },
        "rating": "Strong" if total >= 70 else "Good" if total >= 50 else "Fair" if total >= 35 else "Weak",
    }
