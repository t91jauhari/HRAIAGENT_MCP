import os
import json
import re

import requests
from dataclasses import dataclass
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class HFConfig:
    """
    Configuration for Hugging Face API client, loaded from .env
    """
    model_name: str = os.getenv("HF_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
    api_url: str = os.getenv("HF_API_URL", "https://api-inference.huggingface.co/v1/chat/completions")
    api_token: str = os.getenv("HF_TOKEN") or os.getenv("HF_API_KEY", "")
    temperature: float = float(os.getenv("HF_TEMP", "0"))
    max_tokens: int = int(os.getenv("HF_MAX_NEW", "512"))


class HFModelClient:
    """
    Wrapper for Hugging Face Inference API (chat/completions endpoint).
    - Default model: HF_MODEL (Meta-Llama-3-8B-Instruct)
    - Autonomous mode model: HF_AUTONOMUS_MODEL (e.g., DeepSeek R1 Distill)
    """

    def __init__(self, cfg: Optional[HFConfig] = None, use_autonomous: bool = False):
        if cfg:
            self.cfg = cfg
        else:
            # Load default config from env
            model_name = os.getenv("HF_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")

            # If autonomous mode → override with HF_AUTONOMUS_MODEL if present
            if use_autonomous:
                model_name = os.getenv("HF_AUTONOMUS_MODEL", model_name)

            self.cfg = HFConfig(model_name=model_name)

        if not self.cfg.api_token:
            raise RuntimeError("HF_TOKEN (or HF_API_KEY) is required in .env")

        self.headers = {
            "Authorization": f"Bearer {self.cfg.api_token}",
            "Content-Type": "application/json"
        }

    def _call(self, system: str, user: str) -> str:
        payload = {
            "model": self.cfg.model_name,
            "temperature": self.cfg.temperature,
            "max_tokens": self.cfg.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        r = requests.post(self.cfg.api_url, headers=self.headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()

        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
            elif "text" in choice:
                return choice["text"]
        return ""

    def _strip_think_tags(self, text: str) -> str:
        """Remove <think>...</think> from reasoning model output."""
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def chat_text(self, system: str, user: str) -> str:
        """Return raw text response"""
        return self._call(system, user)

    def chat_json(self, system: str, user: str) -> Dict[str, Any]:
        """Return JSON-parsed response. Guardrails enforce JSON only."""
        guard = "You MUST return ONLY a valid JSON object."
        text = self._call(system, f"{user}\n{guard}")
        try:
            s, e = text.find("{"), text.rfind("}")
            return json.loads(text[s:e+1]) if s != -1 and e != -1 else {}
        except Exception:
            return {}

    def chat_json_reasoning(self, system: str, user: str) -> Dict[str, Any]:
        """
        Reasoning-safe JSON parsing.
        Strips <think> tags before parsing.
        Used by autonomous flow (planner, reflection).
        """
        guard = "You MUST return ONLY a valid JSON object."
        text = self._call(system, f"{user}\n{guard}")
        text = self._strip_think_tags(text)
        try:
            s, e = text.find("{"), text.rfind("}")
            return json.loads(text[s:e + 1]) if s != -1 and e != -1 else {}
        except Exception:
            return {}
