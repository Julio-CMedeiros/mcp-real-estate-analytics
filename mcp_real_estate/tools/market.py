"""Market tools - area-level analytics, price trends, area comparison."""

from ..database import get_connection
from ..tool_groups import ToolGroup
from .registry import make_tool_registrar


TOOLS = {}
_register = make_tool_registrar(ToolGroup.MARKET, TOOLS)


@_register(
    name="get_market_summary",
    description="Get current market snapshot for a neighborhood: avg price/m², active listings, avg days on market, and recent sales volume.",
    input_schema={
        "type": "object",
        "properties": {
            "neighborhood_id": {"type": "integer", "description": "Neighborhood identifier"},
        },
        "required": ["neighborhood_id"],
    },
)
def get_market_summary(neighborhood_id: int) -> dict:
    conn = get_connection()
    # Latest snapshot
    latest = conn.execute(
        "SELECT ms.*, n.name as neighborhood_name, n.city "
        "FROM market_snapshots ms "
        "JOIN neighborhoods n ON ms.neighborhood_id = n.id "
        "WHERE ms.neighborhood_id = ? "
        "ORDER BY ms.month DESC LIMIT 1",
        [neighborhood_id],
    ).fetchone()

    if not latest:
        return {"error": "No market data for this neighborhood"}

    # Previous month for comparison
    previous = conn.execute(
        "SELECT * FROM market_snapshots "
        "WHERE neighborhood_id = ? AND month < ? "
        "ORDER BY month DESC LIMIT 1",
        [neighborhood_id, latest["month"]],
    ).fetchone()

    result = {
        "neighborhood": latest["neighborhood_name"],
        "city": latest["city"],
        "month": latest["month"],
        "avg_price_per_m2": latest["avg_price_m2"],
        "active_listings": latest["listings_count"],
        "avg_days_on_market": latest["avg_days_on_market"],
        "sold_last_month": latest["sold_count"],
    }

    if previous:
        result["mom_price_change_pct"] = round(
            ((latest["avg_price_m2"] - previous["avg_price_m2"]) / previous["avg_price_m2"]) * 100,
            2,
        )
        result["mom_inventory_change"] = latest["listings_count"] - previous["listings_count"]

    return result


@_register(
    name="get_price_trends",
    description="Get monthly price per m² trends for a neighborhood over the last 6 months. Useful for spotting appreciation patterns.",
    input_schema={
        "type": "object",
        "properties": {
            "neighborhood_id": {"type": "integer", "description": "Neighborhood identifier"},
            "months": {"type": "integer", "description": "Number of months to look back (default: 6)", "default": 6},
        },
        "required": ["neighborhood_id"],
    },
)
def get_price_trends(neighborhood_id: int, months: int = 6) -> dict:
    conn = get_connection()
    rows = conn.execute(
        "SELECT ms.*, n.name as neighborhood_name "
        "FROM market_snapshots ms "
        "JOIN neighborhoods n ON ms.neighborhood_id = n.id "
        "WHERE ms.neighborhood_id = ? "
        "ORDER BY ms.month DESC LIMIT ?",
        [neighborhood_id, months],
    ).fetchall()

    if not rows:
        return {"error": "No trend data available"}

    data_points = [
        {
            "month": r["month"],
            "avg_price_m2": r["avg_price_m2"],
            "listings": r["listings_count"],
            "sold": r["sold_count"],
            "days_on_market": r["avg_days_on_market"],
        }
        for r in reversed(rows)  # chronological order
    ]

    first = data_points[0]["avg_price_m2"]
    last = data_points[-1]["avg_price_m2"]

    return {
        "neighborhood": rows[0]["neighborhood_name"],
        "data_points": data_points,
        "period_appreciation_pct": round(((last - first) / first) * 100, 2),
    }


@_register(
    name="compare_areas",
    description="Side-by-side market comparison of two neighborhoods. Compare avg price/m², inventory, time-to-sell, and sales velocity.",
    input_schema={
        "type": "object",
        "properties": {
            "neighborhood_id_a": {"type": "integer", "description": "First neighborhood ID"},
            "neighborhood_id_b": {"type": "integer", "description": "Second neighborhood ID"},
        },
        "required": ["neighborhood_id_a", "neighborhood_id_b"],
    },
)
def compare_areas(neighborhood_id_a: int, neighborhood_id_b: int) -> dict:
    conn = get_connection()

    def _latest(nid):
        return conn.execute(
            "SELECT ms.*, n.name, n.city, n.population "
            "FROM market_snapshots ms "
            "JOIN neighborhoods n ON ms.neighborhood_id = n.id "
            "WHERE ms.neighborhood_id = ? ORDER BY month DESC LIMIT 1",
            [nid],
        ).fetchone()

    a = _latest(neighborhood_id_a)
    b = _latest(neighborhood_id_b)

    if not a or not b:
        return {"error": "Market data missing for one or both neighborhoods"}

    def _summary(row):
        return {
            "neighborhood": row["name"],
            "city": row["city"],
            "avg_price_m2": row["avg_price_m2"],
            "listings": row["listings_count"],
            "avg_days_on_market": row["avg_days_on_market"],
            "sold_last_month": row["sold_count"],
        }

    return {
        "area_a": _summary(a),
        "area_b": _summary(b),
        "price_difference_pct": round(
            ((a["avg_price_m2"] - b["avg_price_m2"]) / b["avg_price_m2"]) * 100, 1
        ),
    }
