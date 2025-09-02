from typing import List, Dict, Any
from app.intent.hf_client import HFModelClient
import langdetect


class ResponseBuilder:
    """
    Builds final natural language response.
    Supports clarification when args are missing.
    Supports bilingual output (Bahasa Indonesia / English).
    """

    def __init__(self):
        self.hf_client = HFModelClient(use_autonomous=False)

    def detect_language(self, text: str) -> str:
        try:
            lang = langdetect.detect(text)
            return "id" if lang == "id" else "en"
        except Exception:
            return "en"

    def build(self, user_message: str, results: List[Dict[str, Any]], reflection: str = "") -> str:
        lang = self.detect_language(user_message)

        for r in results:
            if r["result"].get("clarification_required"):
                missing = r["result"]["missing_args"]
                if lang == "id":
                    return f"Saya butuh informasi tambahan: {', '.join(missing)}. Bisa tolong lengkapi?"
                else:
                    return f"I still need more information: {', '.join(missing)}. Could you please provide it?"

        # Normal response
        if lang == "id":
            system_prompt = (
                "Anda adalah asisten HR. Jawab dalam Bahasa Indonesia yang singkat, jelas, dan sopan. "
                "Gunakan hasil tools dan pertimbangkan refleksi jika ada."
            )
        else:
            system_prompt = (
                "You are an HR assistant. Answer in short, clear, polite English. "
                "Use tool results and consider reflection if provided."
            )

        user_prompt = f"User: {user_message}\nResults: {results}\nReflection: {reflection}"

        return self.hf_client.chat_text(system_prompt, user_prompt)
