"""Tool group definitions and authorization-based filtering.

Groups control which tools are visible to an agent based on its role
or JWT claims. This pattern scales to 20+ tools by keeping visibility
logic separate from tool implementation.
"""

from enum import Enum


class ToolGroup(Enum):
    PROPERTIES = "PROPERTIES"
    MARKET = "MARKET"
    NEIGHBORHOODS = "NEIGHBORHOODS"
    INVESTMENTS = "INVESTMENTS"


# Public-facing agents get these groups
PUBLIC_GROUPS = {ToolGroup.PROPERTIES, ToolGroup.NEIGHBORHOODS}

# Authenticated agents get everything except investment tools
STANDARD_GROUPS = {ToolGroup.PROPERTIES, ToolGroup.MARKET, ToolGroup.NEIGHBORHOODS}

# Internal/analyst agents get full access
ALL_GROUPS = set(ToolGroup)


def get_tools_for_role(
    all_tools: dict,
    role: str = "standard",
) -> dict:
    """Filter tools based on agent role.

    Parameters
    ----------
    all_tools : dict
        Mapping of tool_name -> tool definition dict.
    role : str
        One of 'public', 'standard', 'analyst'.

    Returns
    -------
    dict
        Filtered tool mapping containing only tools the role can access.
    """
    group_map = {
        "public": PUBLIC_GROUPS,
        "standard": STANDARD_GROUPS,
        "analyst": ALL_GROUPS,
    }
    allowed = group_map.get(role, STANDARD_GROUPS)
    return {
        name: tool
        for name, tool in all_tools.items()
        if tool["group"] in allowed
    }
