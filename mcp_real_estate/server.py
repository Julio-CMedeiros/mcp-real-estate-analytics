"""MCP server setup and tool registration."""

import json
from mcp.server import Server
from mcp.types import Tool, TextContent

from .tools.properties import TOOLS as property_tools
from .tools.market import TOOLS as market_tools
from .tools.neighborhoods import TOOLS as neighborhood_tools
from .tools.investments import TOOLS as investment_tools
from .tool_groups import get_tools_for_role

# Aggregate all tools from every group
ALL_TOOLS = {
    **property_tools,
    **market_tools,
    **neighborhood_tools,
    **investment_tools,
}


def create_server() -> Server:
    """Create and configure the MCP server with all tools registered."""
    server = Server("mcp-real-estate-analytics")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools, filtered by agent role.

        In a production system, the role would come from JWT claims
        or request context. Here we default to 'analyst' (full access).
        """
        visible = get_tools_for_role(ALL_TOOLS, role="analyst")
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["input_schema"],
            )
            for t in visible.values()
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Execute a tool by name with the given arguments."""
        if name not in ALL_TOOLS:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

        tool = ALL_TOOLS[name]
        try:
            result = tool["handler"](**arguments)
            return [TextContent(type="text", text=json.dumps(result, default=str))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    return server
