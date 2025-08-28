import logging
from typing import List, Dict, Any
from app.graph.mcp_client import mcp_client
from app.graph.clarifier import get_missing_args
from app.graph.schema_utils import extract_schema
from app.memory.session_store import SessionStore

logger = logging.getLogger("app.graph.multi_intent_planner")
async def execute_intents(
    intents: List[Dict[str, Any]],
    session_store: SessionStore,
    session_id: str
) -> Dict[str, Any]:
    """
    Executes multiple intents in the natural order provided by Hugging Face.
    Uses MCP tools for execution and clarifies missing arguments if needed.

    Args:
        intents: List of intent dicts
        session_store: SessionStore instance to persist history.
        session_id: Current session identifier.

    Returns:
        dict with aggregated results
    """
    results: Dict[str, Any] = {}
    logger.info(f"[MULTI-INTENT] Starting execution for {len(intents)} intents.")

    # Preload available tools
    tools = await mcp_client.list_tools()
    tool_names = [t.name.strip().lower() for t in tools]

    for intent in intents:
        intent_name = intent["name"].strip().lower()
        args = intent.get("args", {}) or {}
        logger.debug(f"[MULTI-INTENT] Processing {intent_name} with args={args}")

        # ---- Tool matching ----
        if intent_name not in tool_names:
            logger.warning(f"[MULTI-INTENT] No matching MCP tool for {intent_name}")
            # Flag fallback so ResponseBuilder handles it gracefully
            results["fallback"] = {
                "status": "not_found",
                "intent": intent_name,
                "message": f"Tidak ada tool untuk intent '{intent_name}'"
            }
            continue

        # ---- Extract schema ----
        tool = next(t for t in tools if t.name.strip().lower() == intent_name)
        schema = extract_schema(tool)
        required = schema.get("required", [])

        # Normalize args → always include required keys
        normalized_args = {k: args.get(k) for k in required}

        # ---- Clarify missing values ----
        missing = await get_missing_args(intent_name, normalized_args)
        if missing:
            logger.warning(f"[MULTI-INTENT] Missing args for {intent_name}: {missing}")
            results[intent_name] = {
                "status": "clarification_needed",
                "missing": missing
            }
            session_store.add_clarification(session_id, intent_name, missing)
            continue

        # ---- Execute tool ----
        try:
            result = await mcp_client.call(intent_name, normalized_args)
            logger.info(f"[MULTI-INTENT] Executed {intent_name} successfully.")

            results[intent_name] = {"status": "success", "result": result}
            session_store.add_tool_call(session_id, intent_name, normalized_args, result)

        except Exception as e:
            logger.error(f"[MULTI-INTENT] Failed {intent_name}: {str(e)}", exc_info=True)
            results[intent_name] = {"status": "error", "error": str(e)}

    return results
