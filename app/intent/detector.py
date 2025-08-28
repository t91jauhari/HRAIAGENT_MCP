import logging
from typing import Dict, Any
from app.intent.hf_client import HFModelClient, HFConfig
from app.prompts import build_dynamic_intent_prompt

logger = logging.getLogger("app.intent.detector")


class IntentDetector:
    """
    Detects intents using Hugging Face model client.
    """

    def __init__(self):
        self.client = HFModelClient(HFConfig())

    async def detect(self, user_message: str, memory_summary: str = "") -> Dict[str, Any]:
        """
        Detect intent(s) for a user message + memory context.
        Builds schema-aware prompt dynamically from MCP.
        """
        system_prompt = await build_dynamic_intent_prompt()

        # Log the full dynamic system prompt for debugging
        logger.debug(
            "[HF-DETECTOR] --- Dynamic Intent Prompt Start ---\n"
            f"{system_prompt}\n"
            "[HF-DETECTOR] --- Dynamic Intent Prompt End ---"
        )

        # Combine with conversation context
        prompt = f"""{system_prompt}

Conversation memory:
{memory_summary}

User message:
{user_message}
"""

        logger.debug(f"[HF-DETECTOR] Final composed prompt=\n{prompt}")

        # Call the HF client
        result = self.client.chat_json(system_prompt, prompt)

        logger.info(f"[HF-DETECTOR] detected intents={result.get('intents', [])}")
        return result
