import logging
import json
from typing import Dict, Any, Optional, List
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger("app.graph.mcp_client")


def make_json_block(data: dict) -> dict:
    """
    Create a JSON-compatible MCP ContentBlock.
    """
    try:
        from mcp.types import JsonContent
        return JsonContent(type="json", data=data)
    except ImportError:
        from mcp.types import TextContent
        return TextContent(type="text", text=json.dumps(data))


class MCPToolClient:
    """
    Wrapper around MCP client.
    Manages a session with the MCP server and provides tool calls.
    Always normalizes tools to a plain list[Tool].
    """

    def __init__(self):
        self.params = StdioServerParameters(
            command="python",
            args=["-m", "mcp_server.server", "stdio"],
            env={"PYTHONPATH": "/app", **os.environ},
        )
        self.session: Optional[ClientSession] = None
        self._ctx = None
        self._aio = None

    async def start(self):
        """Start MCP subprocess + session once."""
        if self.session:
            return

        logger.info("[MCP-CLIENT] Starting MCP server subprocess...")
        self._ctx = stdio_client(self.params)
        self._aio = self._ctx.__aenter__()
        read, write = await self._aio
        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()
        logger.info("[MCP-CLIENT] MCP session initialized successfully.")

        raw_tools = await self.session.list_tools()
        parsed = (
            raw_tools if isinstance(raw_tools, list)
            else getattr(raw_tools, "tools", [])
        )
        logger.info(f"[MCP-CLIENT] Tools available at startup: {[t.name for t in parsed]}")

    async def stop(self):
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None
        if self._ctx:
            await self._ctx.__aexit__(None, None, None)
        logger.info("[MCP-CLIENT] MCP session stopped.")

    async def list_tools(self):
        """Always return plain list[Tool]."""
        await self.start()
        raw_tools = await self.session.list_tools()
        if isinstance(raw_tools, list):
            parsed = raw_tools
        elif hasattr(raw_tools, "tools"):
            parsed = list(raw_tools.tools)
        else:
            parsed = []
        logger.debug(f"[MCP-CLIENT] list_tools → {[t.name for t in parsed]}")
        return parsed

    async def call(self, tool: str, args: Dict[str, Any]) -> Any:
        """Call an MCP tool and unwrap results into plain dicts/values."""
        await self.start()
        safe_tool = tool.strip().lower()
        logger.info(f"[MCP-CLIENT] Calling tool '{safe_tool}' with args={args}")

        try:
            res = await self.session.call_tool(safe_tool, arguments=args)

            blocks: List[Any] = (
                    getattr(res, "outputs", None)
                    or getattr(res, "structuredContent", None)
                    or getattr(res, "content", None)
                    or []
            )

            if not blocks:
                logger.warning(f"[MCP-CLIENT] Tool '{safe_tool}' returned no content blocks.")
                return []

            results = []
            for idx, block in enumerate(blocks):
                logger.debug(f"[MCP-CLIENT] Raw block[{idx}] = {block!r}")

                if hasattr(block, "type"):
                    logger.debug(f"[MCP-CLIENT] Block[{idx}].type={block.type}")
                    if block.type == "json":
                        results.append(getattr(block, "data", None))
                    elif block.type == "text":
                        txt = getattr(block, "text", "")
                        logger.debug(f"[MCP-CLIENT] Block[{idx}].text={txt!r}")
                        try:
                            results.append(json.loads(txt))
                        except Exception as e:
                            logger.warning(f"[MCP-CLIENT] Failed to parse block[{idx}] text as JSON: {e}")
                            results.append(txt)
                    else:
                        results.append(block)

                elif isinstance(block, dict):
                    logger.debug(f"[MCP-CLIENT] Block[{idx}] is dict")
                    btype = block.get("type")
                    if btype == "json":
                        results.append(block.get("data"))
                    elif btype == "text":
                        txt = block.get("text", "")
                        logger.debug(f"[MCP-CLIENT] Block[{idx}]['text']={txt!r}")
                        try:
                            results.append(json.loads(txt))
                        except Exception as e:
                            logger.warning(f"[MCP-CLIENT] Failed to parse dict block[{idx}] text as JSON: {e}")
                            results.append(txt)
                    else:
                        results.append(block)

                else:
                    results.append(block)

            if results:
                logger.info(f"[MCP-CLIENT] Tool '{safe_tool}' executed successfully. Parsed results={results}")
            else:
                logger.warning(f"[MCP-CLIENT] Tool '{safe_tool}' produced blocks but no parsed results.")

            return results[0] if len(results) == 1 else results

        except Exception as e:
            logger.error(f"[MCP-CLIENT] Error while calling tool '{safe_tool}': {e}", exc_info=True)
            raise

    async def call_tool(self, tool: str, args: Dict[str, Any], as_json: bool = True) -> Dict[str, Any]:
        result = await self.call(tool, args)

        if as_json:
            if isinstance(result, dict):
                return result
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except Exception:
                    # Standardize plain string into dict for safety
                    return {"raw_text": result}
            raise ValueError(f"Tool {tool} did not return dict/JSON.")
        return result


mcp_client = MCPToolClient()
