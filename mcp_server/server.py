import sys
import anyio
import logging
from mcp.server.lowlevel import Server
from . import hr_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mcp_server")


def main(transport: str = "stdio"):
    app = Server("hr-ai-mcp")

    @app.call_tool()
    async def _call_tool(name: str, arguments: dict):
        return await hr_tools.call_tool(name, arguments)

    @app.list_tools()
    async def _list_tools():
        tools = await hr_tools.list_tools()
        logger.info(f"[MCP-SERVER] Registered tools: {[t.name for t in tools]}")
        return tools

    if transport == "stdio":
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())

        anyio.run(arun)
    else:
        raise ValueError("Only stdio transport is supported right now.")


if __name__ == "__main__":
    mode = (sys.argv[1] if len(sys.argv) > 1 else "stdio").lower()
    main(mode)
