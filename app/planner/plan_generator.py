import json
from typing import List, Dict, Any

from app.intent.hf_client import HFModelClient
from app.graph.mcp_client import mcp_client
from app.graph.schema_utils import extract_schema


class PlanGenerator:
    """
    Generates a multi-step JSON plan using a reasoning model (DeepSeek).
    Reads enriched tool metadata (descriptions, examples, keywords)
    from MCP and injects it into the planning prompt.
    """

    def __init__(self):
        self.hf_client = HFModelClient(use_autonomous=True)

    async def generate_plan(self, user_message: str) -> List[Dict[str, Any]]:
        tools = await mcp_client.list_tools()

        tool_descriptions = []
        for t in tools:
            schema = extract_schema(t)
            args_schema = json.dumps(schema.get("properties", {}), indent=2)
            required = schema.get("required", [])
            examples = getattr(t, "examples", None)
            keywords = getattr(t, "keywords", None)

            section = [
                f"- {t.name}: {t.description}",
                f"  Required args: {', '.join(required) if required else 'none'}",
                f"  Args schema: {args_schema}"
            ]
            if examples:
                section.append(f"  Examples: {examples}")
            if keywords:
                section.append(f"  Keywords: {keywords}")

            tool_descriptions.append("\n".join(section))

        # 🔹 Strong system prompt
        system_prompt = (
            "You are an AUTONOMOUS HR PLANNING AGENT.\n"
            "Users will ask HR-related questions in Bahasa Indonesia, English, "
            "and sometimes informal slang (e.g., 'ajuin cuti donk').\n\n"
            "Your task is to output a JSON plan that maps the query to available HR tools.\n"
            "The plan must be an ordered array of steps. Each step has:\n"
            "  - 'action': tool name (must match exactly one available tool)\n"
            "  - 'args': dictionary of arguments\n\n"
            "Available tools with descriptions, args, examples, and keywords:\n"
            f"{chr(10).join(tool_descriptions)}\n\n"
            "STRICT RULES:\n"
            "1. Output ONLY valid JSON — no explanations, no <think> tags.\n"
            "2. Always include all required args. If a value is unknown, set it to null.\n"
            "3. Use employee_id='E-001' if not provided by the user (for testing).\n"
            "4. Choose the correct tool based on meaning:\n"
            "   - Use 'leave_balance' for remaining quota (e.g., 'sisa cuti').\n"
            "   - Use 'leave_status' for approval state (e.g., 'sudah disetujui belum').\n"
            "   - Use 'payroll_lookup' for single-period payroll.\n"
            "   - Use 'payroll_history' for multiple months.\n"
            "5. If the query requires multiple checks (e.g., salary deduction), include multiple steps.\n\n"
            "EXAMPLES:\n"
            "User: \"ajuin cuti donk\"\n"
            "{\n"
            "  \"plan\": [\n"
            "    {\n"
            "      \"action\": \"leave_request\",\n"
            "      \"args\": {\"employee_id\": \"E-001\", \"start\": null, \"end\": null, \"leave_type\": \"annual\", \"reason\": null}\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            "User: \"kenapa gaji saya bulan ini berkurang?\"\n"
            "{\n"
            "  \"plan\": [\n"
            "    {\"action\": \"payroll_lookup\", \"args\": {\"employee_id\": \"E-001\", \"period\": \"2025-08\"}},\n"
            "    {\"action\": \"deduction_reason\", \"args\": {\"employee_id\": \"E-001\", \"period\": \"2025-08\"}},\n"
            "    {\"action\": \"leave_balance\", \"args\": {\"employee_id\": \"E-001\"}}\n"
            "  ]\n"
            "}\n"
        )

        user_prompt = f"User query: \"{user_message}\"\nGenerate plan now."

        result = self.hf_client.chat_json_reasoning(system_prompt, user_prompt)

        return result.get("plan", []) if isinstance(result, dict) else []
