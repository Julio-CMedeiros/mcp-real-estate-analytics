"""Shared utilities for tool registration."""

from ..tool_groups import ToolGroup


def make_tool_registrar(group: ToolGroup, tools_dict: dict):
    """Create a registration decorator scoped to a specific tool group.

    Usage in each tool module:
        TOOLS = {}
        _register = make_tool_registrar(ToolGroup.PROPERTIES, TOOLS)

        @_register(name="search_properties", description="...", input_schema={...})
        def search_properties(...): ...
    """

    def registrar(name: str, description: str, input_schema: dict):
        def decorator(fn):
            tools_dict[name] = {
                "name": name,
                "description": description,
                "input_schema": input_schema,
                "group": group,
                "handler": fn,
            }
            return fn
        return decorator

    return registrar
