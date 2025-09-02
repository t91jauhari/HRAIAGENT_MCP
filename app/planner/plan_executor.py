from typing import List, Dict, Any
from app.graph.mcp_client import mcp_client
import logging

logger = logging.getLogger("autonomous.plan_executor")


class PlanExecutor:
    """
    Executes a multi-step plan by calling MCP tools.
    If required args are missing, triggers clarification instead of execution.
    """

    async def execute(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []

        for idx, step in enumerate(plan):
            action = step.get("action")
            args = step.get("args", {})

            logger.info(f"[EXEC] Step {idx+1}: validating '{action}' with args={args}")
            missing = [k for k, v in args.items() if v is None]
            if missing:
                logger.warning(f"[EXEC] Step {idx+1}: Missing args {missing}, clarification required.")
                results.append({
                    "action": action,
                    "args": args,
                    "result": {
                        "clarification_required": True,
                        "missing_args": missing
                    }
                })
                continue

            logger.info(f"[EXEC] Step {idx+1}: executing tool '{action}'")
            result = await mcp_client.call(action, args)

            # Normalize
            if isinstance(result, dict):
                normalized = result
            else:
                normalized = {"raw_text": str(result)}

            results.append({
                "action": action,
                "args": args,
                "result": normalized
            })

            logger.info(f"[EXEC] Step {idx+1}: result={normalized}")

        return results
