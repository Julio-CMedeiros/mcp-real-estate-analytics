"""MCP Real Estate Analytics Server - entry point."""

import argparse
from .server import create_server


def main():
    parser = argparse.ArgumentParser(description="MCP Real Estate Analytics Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument("--port", type=int, default=3001, help="Port for SSE transport")
    args = parser.parse_args()

    server = create_server()

    if args.transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount
        import uvicorn

        sse = SseServerTransport("/messages/")
        starlette_app = Starlette(
            routes=[
                Route("/sse", endpoint=sse.handle_sse_connection),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )
        uvicorn.run(starlette_app, host="0.0.0.0", port=args.port)
    else:
        import asyncio
        from mcp.server.stdio import stdio_server

        async def run_stdio():
            async with stdio_server() as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options(),
                )

        asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
