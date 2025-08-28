from typing import List, Dict
from .mcp_client import mcp_client
from .schema_utils import extract_schema
import logging
import json

logger = logging.getLogger("app.graph.clarifier")


async def get_missing_args(intent: str, given_args: Dict) -> List[str]:
    """
    Inspect MCP schema to determine required args missing from the user's input.
    Works with dicts, Pydantic models, and legacy schemas.
    """
    tools = await mcp_client.list_tools()   # always a list[Tool]
    for t in tools:
        if t.name == intent:
            schema = extract_schema(t)
            required = schema.get("required", [])

            # Log full schema and arguments for debug traceability
            logger.debug(
                "[CLARIFIER] Tool=%s schema=%s given_args=%s",
                t.name,
                json.dumps(schema, ensure_ascii=False, indent=2),
                json.dumps(given_args, ensure_ascii=False, indent=2)
            )

            missing = [
                r for r in required
                if r not in given_args or given_args[r] is None or given_args[r] == ""
            ]

            if missing:
                logger.info(f"[CLARIFIER] Missing args for {intent}: {missing}")
            else:
                logger.debug(f"[CLARIFIER] No missing args for {intent}")

            return missing
    return []
