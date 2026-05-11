# 🏠 MCP Real Estate Analytics Server

A **Model Context Protocol (MCP)** server that exposes real estate market data and analytics to AI agents through structured tools. Built as a reference implementation demonstrating MCP tool design patterns, group-based authorization, and schema best practices.

## What is MCP?

[Model Context Protocol](https://modelcontextprotocol.io/) is an open standard for connecting AI agents to external data and tools. Instead of stuffing everything into a prompt, MCP lets agents discover and call structured tools, essentially an API designed for LLMs.

## Architecture

```
┌─────────────────────────────────────────────┐
│              AI Agent / LLM                 │
└──────────────┬──────────────────────────────┘
               │ MCP Protocol (JSON-RPC)
┌──────────────▼──────────────────────────────┐
│         MCP Server (this project)           │
│                                             │
│  ┌───────────────┐  ┌────────────────────┐  │
│  │  Tool Groups  │  │  Auth & Filtering  │  │
│  │               │  │                    │  │
│  │ • Properties  │  │ • JWT claims       │  │
│  │ • Market      │  │ • Tool groups      │  │
│  │ • Neighborhood│  │ • Role scoping     │  │
│  │ • Investment  │  │                    │  │
│  └──────┬────────┘  └────────────────────┘  │
│         │                                   │
│  ┌──────▼──────┐                            │
│  │  Database   │                            │
│  │  (SQLite)   │                            │
│  └─────────────┘                            │
└─────────────────────────────────────────────┘
```

## Features

- **10 tools** across 4 groups: Properties, Market, Neighborhoods, Investments
- **Tool group filtering** - agents only see tools matching their authorization level
- **Structured output schemas** - every tool returns typed, documented data
- **Seed data** - built-in demo dataset (Lisbon metro area) for testing without external dependencies
- **Dual transport** - stdio (agent integration) and SSE (browser testing)

## Tools

| Tool | Group | Description |
|------|-------|-------------|
| `search_properties` | Properties | Search listings by area, type, price range, bedrooms |
| `get_property_details` | Properties | Full property details including features, description, and listing status |
| `get_price_history` | Properties | Historical price changes for a specific property |
| `get_market_summary` | Market | Avg price/m², inventory, days-on-market for an area |
| `get_price_trends` | Market | Price per m² trends over time for an area |
| `compare_areas` | Market | Side-by-side market comparison of two neighborhoods |
| `get_neighborhood_profile` | Neighborhoods | Demographics, amenities, transport, safety scores |
| `list_nearby_amenities` | Neighborhoods | Schools, hospitals, transport stops within radius |
| `estimate_rental_yield` | Investments | Gross/net rental yield estimate for a property |
| `get_investment_score` | Investments | Composite score based on yield, appreciation, demand |

## Quick Start

```bash
# Install
pip install -e .

# Run with stdio transport (for AI agent integration)
python -m mcp_real_estate

# Run with SSE transport (for browser/inspector testing)
python -m mcp_real_estate --transport sse --port 3001
```

### Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python -m mcp_real_estate
```

## Tool Design Principles

Patterns applied in this project (and in production MCP servers I've built with 20+ tools):

### 1. Naming - `action_entity_modifier`
```
search_properties           ✅  clear action + entity
get_market_summary          ✅  retrieval + scope
estimate_rental_yield       ✅  computation + domain term
get_data                    ❌  too vague for LLM tool selection
```

### 2. Descriptions
- Under 160 chars. LLMs parse these for tool selection
- **What** and **why**, never implementation details
- Include key params and business context
- End with a use case when it helps disambiguation

### 3. Tool Groups & Authorization
```python
class ToolGroup(Enum):
    PROPERTIES = "PROPERTIES"       # Listing search and details
    MARKET = "MARKET"               # Area-level market analytics
    NEIGHBORHOODS = "NEIGHBORHOODS" # Location intelligence
    INVESTMENTS = "INVESTMENTS"     # Financial analysis (restricted)
```
Groups let you filter visibility per agent role. A public-facing agent gets Properties + Neighborhoods; an internal analyst agent gets everything including Investments.

### 4. Structured Outputs
Every tool returns a typed dict with consistent shapes. No free-text dumps. This lets agents parse results reliably and chain tools together.

## Project Structure

```
mcp_real_estate/
├── __main__.py          # Entry point, transport selection
├── server.py            # MCP server setup, tool registration
├── tool_groups.py       # Group definitions, auth filtering
├── database.py          # SQLite connection + seed data (Lisbon metro area)
└── tools/
    ├── properties.py    # Listing search, details, history
    ├── market.py        # Area-level analytics, trends
    ├── neighborhoods.py # Location profiles, amenities
    └── investments.py   # Yield estimates, scoring
```

## License

MIT
