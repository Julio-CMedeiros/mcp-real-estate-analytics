"""Neighborhood tools - profiles and amenity search."""

from ..database import get_connection
from ..tool_groups import ToolGroup
from .registry import make_tool_registrar


TOOLS = {}
_register = make_tool_registrar(ToolGroup.NEIGHBORHOODS, TOOLS)


@_register(
    name="get_neighborhood_profile",
    description="Get a neighborhood's full profile: demographics, income level, safety, transport, and walkability scores.",
    input_schema={
        "type": "object",
        "properties": {
            "neighborhood_id": {"type": "integer", "description": "Neighborhood identifier"},
        },
        "required": ["neighborhood_id"],
    },
)
def get_neighborhood_profile(neighborhood_id: int) -> dict:
    conn = get_connection()
    r = conn.execute(
        "SELECT * FROM neighborhoods WHERE id = ?",
        [neighborhood_id],
    ).fetchone()

    if not r:
        return {"error": "Neighborhood not found"}

    # Count amenities by type
    amenity_counts = conn.execute(
        "SELECT type, COUNT(*) as count FROM amenities "
        "WHERE neighborhood_id = ? GROUP BY type",
        [neighborhood_id],
    ).fetchall()

    return {
        "id": r["id"],
        "name": r["name"],
        "city": r["city"],
        "population": r["population"],
        "avg_income": r["avg_income"],
        "scores": {
            "safety": r["safety_score"],
            "transport": r["transport_score"],
            "walkability": r["walkability_score"],
        },
        "amenities_summary": {
            row["type"]: row["count"] for row in amenity_counts
        },
    }


@_register(
    name="list_nearby_amenities",
    description="List schools, hospitals, metro stations, parks, and other amenities near a neighborhood. Filter by type and max distance.",
    input_schema={
        "type": "object",
        "properties": {
            "neighborhood_id": {"type": "integer", "description": "Neighborhood identifier"},
            "amenity_type": {
                "type": "string",
                "description": "Filter by type",
                "enum": ["school", "hospital", "metro", "supermarket", "park", "gym"],
            },
            "max_distance_km": {
                "type": "number",
                "description": "Maximum distance in km (default: 2.0)",
                "default": 2.0,
            },
        },
        "required": ["neighborhood_id"],
    },
)
def list_nearby_amenities(
    neighborhood_id: int,
    amenity_type: str = None,
    max_distance_km: float = 2.0,
) -> dict:
    conn = get_connection()
    query = "SELECT * FROM amenities WHERE neighborhood_id = ? AND distance_km <= ?"
    params: list = [neighborhood_id, max_distance_km]

    if amenity_type:
        query += " AND type = ?"
        params.append(amenity_type)

    query += " ORDER BY distance_km ASC"
    rows = conn.execute(query, params).fetchall()

    return {
        "amenities": [
            {
                "name": r["name"],
                "type": r["type"],
                "distance_km": r["distance_km"],
            }
            for r in rows
        ],
        "total": len(rows),
    }
