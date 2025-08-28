from app.graph.mcp_client import mcp_client
from app.graph.schema_utils import extract_schema

async def build_dynamic_intent_prompt() -> str:
    """
    Build system prompt dynamically from MCP tools.
    """
    tools = await mcp_client.list_tools()

    prompt_lines = [
        "You are an intent detection module for an AI HR assistant.",
        "Your job is to map a user query into one or more intents, along with structured arguments.",
        "",
        "Available intents:"
    ]

    for idx, tool in enumerate(tools, start=1):
        schema = extract_schema(tool)
        required = schema.get("required", [])
        prompt_lines.append(f"{idx}. {tool.name}: {tool.description or ''}")
        prompt_lines.append(f"   Required args: {', '.join(required) if required else 'none'}")

    prompt_lines.append(
        """
Output format (STRICT JSON only, no extra text):
{
  "intents": [
    {
      "name": "leave_request",
      "confidence": 0.95,
      "args": {
        "employee_id": "E-001",
        "start": "2025-05-10",
        "end": "2025-05-12",
        "leave_type": "annual"
      }
    }
  ]
}

Rules:
- Always return JSON ONLY.
- Always include **all required args** for the detected intent.
- If a required argument is not provided by the user, set its value to null.
- Do not invent values that the user did not provide.
- If multiple intents exist, include them in "intents" array in execution order.
- Do not explain, only return JSON.
"""
    )

    return "\n".join(prompt_lines)
