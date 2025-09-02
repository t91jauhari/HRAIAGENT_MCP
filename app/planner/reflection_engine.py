from typing import List, Dict, Any
from app.intent.hf_client import HFModelClient


class ReflectionEngine:
    """
    Reflects on tool execution results to check completeness.
    """

    def __init__(self):
        self.hf_client = HFModelClient(use_autonomous=True)

    def reflect(self, user_message: str, results: List[Dict[str, Any]]) -> str:
        system_prompt = (
            "You are a reflection module. "
            "Check if the tool execution results fully answer the user's question. "
            "If something is missing, suggest what else should be checked."
        )
        user_prompt = f"User message: {user_message}\nExecution results: {results}"

        # ✅ Use reasoning-safe plain text
        return self.hf_client.chat_text(system_prompt, user_prompt)
