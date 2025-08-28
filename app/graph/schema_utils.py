import logging
from typing import Dict, Any

logger = logging.getLogger("app.graph.schema_utils")


def extract_schema(tool) -> Dict[str, Any]:
    """
    Extract JSON schema dict from an MCP Tool object.
    Handles dict-based, Pydantic-based, and legacy formats.
    """
    schema = {}

    try:
        if isinstance(tool.inputSchema, dict):
            schema = tool.inputSchema
        elif hasattr(tool.inputSchema, "model_json_schema"):
            schema = tool.inputSchema.model_json_schema()
        elif hasattr(tool.inputSchema, "jsonSchema"):
            schema = tool.inputSchema.jsonSchema
    except Exception as e:
        logger.warning(f"[SCHEMA] Failed to extract schema for tool={getattr(tool, 'name', '?')}: {e}")

    return schema or {}
