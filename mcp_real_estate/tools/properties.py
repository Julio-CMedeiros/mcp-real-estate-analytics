"""Property tools - search, details, price history."""

from ..database import get_connection
from ..tool_groups import ToolGroup
from .registry import make_tool_registrar


TOOLS = {}
_register = make_tool_registrar(ToolGroup.PROPERTIES, TOOLS)


@_register(
    name="search_properties",
    description="Search property listings by area, type, price range, and bedrooms. Returns matching active listings with key details.",
    input_schema={
        "type": "object",
        "properties": {
            "neighborhood": {
                "type": "string",
                "description": "Neighborhood name to search in (e.g., 'Chiado', 'Alfama')",
            },
            "property_type": {
                "type": "string",
                "description": "Property type filter",
                "enum": ["apartment", "house", "studio", "penthouse"],
            },
            "min_price": {"type": "number", "description": "Minimum price in EUR"},
            "max_price": {"type": "number", "description": "Maximum price in EUR"},
            "min_bedrooms": {"type": "integer", "description": "Minimum number of bedrooms"},
        },
        "required": [],
    },
)
def search_properties(
    neighborhood: str = None,
    property_type: str = None,
    min_price: float = None,
    max_price: float = None,
    min_bedrooms: int = None,
) -> dict:
    conn = get_connection()
    query = (
        "SELECT p.*, n.name as neighborhood_name, n.city "
        "FROM properties p "
        "JOIN neighborhoods n ON p.neighborhood_id = n.id "
        "WHERE p.status = 'active'"
    )
    params: list = []

    if neighborhood:
        query += " AND LOWER(n.name) LIKE LOWER(?)"
        params.append(f"%{neighborhood}%")
    if property_type:
        query += " AND p.type = ?"
        params.append(property_type)
    if min_price:
        query += " AND p.price >= ?"
        params.append(min_price)
    if max_price:
        query += " AND p.price <= ?"
        params.append(max_price)
    if min_bedrooms is not None:
        query += " AND p.bedrooms >= ?"
        params.append(min_bedrooms)

    query += " ORDER BY p.price ASC LIMIT 20"
    rows = conn.execute(query, params).fetchall()

    return {
        "results": [
            {
                "id": r["id"],
                "title": r["title"],
                "type": r["type"],
                "neighborhood": r["neighborhood_name"],
                "city": r["city"],
                "price": r["price"],
                "price_per_m2": round(r["price"] / r["area_m2"], 0),
                "area_m2": r["area_m2"],
                "bedrooms": r["bedrooms"],
                "bathrooms": r["bathrooms"],
                "energy_rating": r["energy_rating"],
                "listed_date": r["listed_date"],
            }
            for r in rows
        ],
        "total": len(rows),
    }


@_register(
    name="get_property_details",
    description="Get full details for a specific property including features, description, and listing status.",
    input_schema={
        "type": "object",
        "properties": {
            "property_id": {"type": "integer", "description": "Property identifier"},
        },
        "required": ["property_id"],
    },
)
def get_property_details(property_id: int) -> dict:
    conn = get_connection()
    r = conn.execute(
        "SELECT p.*, n.name as neighborhood_name, n.city "
        "FROM properties p "
        "JOIN neighborhoods n ON p.neighborhood_id = n.id "
        "WHERE p.id = ?",
        [property_id],
    ).fetchone()

    if not r:
        return {"error": "Property not found"}

    return {
        "id": r["id"],
        "title": r["title"],
        "type": r["type"],
        "status": r["status"],
        "neighborhood": r["neighborhood_name"],
        "city": r["city"],
        "price": r["price"],
        "price_per_m2": round(r["price"] / r["area_m2"], 0),
        "area_m2": r["area_m2"],
        "bedrooms": r["bedrooms"],
        "bathrooms": r["bathrooms"],
        "floor": r["floor"],
        "features": {
            "parking": bool(r["has_parking"]),
            "terrace": bool(r["has_terrace"]),
        },
        "energy_rating": r["energy_rating"],
        "listed_date": r["listed_date"],
        "description": r["description"],
    }


@_register(
    name="get_price_history",
    description="Get the price change history for a property. Shows listing, reductions, and sale events over time.",
    input_schema={
        "type": "object",
        "properties": {
            "property_id": {"type": "integer", "description": "Property identifier"},
        },
        "required": ["property_id"],
    },
)
def get_price_history(property_id: int) -> dict:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM price_history WHERE property_id = ? ORDER BY changed_date ASC",
        [property_id],
    ).fetchall()

    if not rows:
        return {"error": "No price history found", "property_id": property_id}

    events = [
        {"price": r["price"], "date": r["changed_date"], "event": r["event"]}
        for r in rows
    ]
    first_price = events[0]["price"]
    last_price = events[-1]["price"]

    return {
        "property_id": property_id,
        "events": events,
        "original_price": first_price,
        "current_price": last_price,
        "total_change_pct": round(((last_price - first_price) / first_price) * 100, 1),
    }
