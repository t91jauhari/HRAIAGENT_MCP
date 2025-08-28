import os
import json
import requests
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv

# ✅ Load variables from .env automatically
load_dotenv()


@dataclass
class HFConfig:
    """
    Configuration for Hugging Face API client, loaded from .env
    """
    model_name: str = os.getenv("HF_MODEL", "")
    api_url: str = os.getenv("HF_API_URL", "")
    api_token: str = os.getenv("HF_TOKEN") or os.getenv("HF_API_KEY", "")
    temperature: float = float(os.getenv("HF_TEMP", "0"))
    max_tokens: int = int(os.getenv("HF_MAX_NEW", "512"))


class HFModelClient:
    """
    Wrapper for Hugging Face Inference API (chat/completions endpoint).
    """

    def __init__(self, cfg: HFConfig = HFConfig()):
        self.cfg = cfg
        if not cfg.api_token:
            raise RuntimeError("HF_TOKEN (or HF_API_KEY) is required in .env")
        self.headers = {
            "Authorization": f"Bearer {cfg.api_token}",
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

    def chat_text(self, system: str, user: str) -> str:
        """Return raw text response"""
        return self._call(system, user)

    def chat_json(self, system: str, user: str) -> Dict[str, Any]:
        """
        Return JSON-parsed response. Guardrails enforce JSON only.
        """
        guard = "You MUST return ONLY a valid JSON object."
        text = self._call(system, f"{user}\n{guard}")
        try:
            s, e = text.find("{"), text.rfind("}")
            return json.loads(text[s:e+1]) if s != -1 and e != -1 else {}
        except Exception:
            return {}
