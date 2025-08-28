import json
import logging
from typing import Dict, List, Any
from app.intent.hf_client import HFModelClient, HFConfig

logger = logging.getLogger("app.graph.response_builder")


class ResponseBuilder:
    """
    Builds assistant responses using Hugging Face LLM.
    Handles:
      - Clarifications
      - Tool results
      - Greetings / fallback
    """

    def __init__(self):
        self.client = HFModelClient(HFConfig())

    def build(
        self,
        results: Dict[str, Any],
        clarifications: List[Dict[str, Any]],
        user_message: str = ""
    ) -> str:
        """
        Build a natural chatbot response with the help of LLM.
        """

        # ---- Case 0: Fallback / no intent ----
        if results.get("fallback"):
            text = user_message.lower()
            greetings = ["halo", "hai", "assalamualaikum", "pagi", "siang", "sore", "malam"]

            if any(g in text for g in greetings):
                return (
                    "Halo! Senang bisa membantu Anda. "
                    "Apakah ada yang ingin ditanyakan terkait HR, seperti cuti, payroll, atau status cuti Anda?"
                )

            # Otherwise, generic polite response via LLM
            system_prompt = (
                "Anda adalah asisten HR yang ramah. "
                "Jika pengguna bertanya hal di luar HR tools (cuti, payroll, status cuti), "
                "tetap jawab dengan sopan dan alami dalam bahasa Indonesia. "
                "Hindari jawaban kaku, tetap bantu menjaga percakapan."
            )
            return self.client.chat_text(system_prompt, user_message)

        # ---- Case 1: Explicit clarifications ----
        if clarifications:
            clarif_text = {"clarifications": clarifications}
            system_prompt = (
                "Anda adalah asisten HR. Permintaan pengguna masih kurang informasi. "
                "Tolong tanyakan field yang hilang dengan sopan dan alami, dalam bahasa Indonesia."
            )
            return self.client.chat_text(system_prompt, json.dumps(clarif_text, ensure_ascii=False))

        # ---- Case 2: Results exist ----
        if results:
            payload = {"results": results}
            system_prompt = (
                "Anda adalah asisten HR. Berdasarkan JSON hasil dari tools berikut, "
                "buat jawaban alami, singkat, dan sopan dalam bahasa Indonesia.\n\n"
                "- Jika hasil adalah pengajuan cuti (leave_request), pastikan menyebutkan ID permintaan, "
                "periode cuti, dan statusnya.\n"
                "- Jika hasil adalah payroll_lookup, jelaskan gaji bersih dan rincian utama secara ringkas.\n"
                "- Jika hasil adalah leave_status, jelaskan sisa cuti per jenis cuti.\n\n"
                "Jangan menambahkan fakta baru, hanya parafrasa data yang ada."
            )
            return self.client.chat_text(system_prompt, json.dumps(payload, ensure_ascii=False))

        # ---- Case 3: Nothing matched ----
        return (
            "Maaf, saya tidak mengerti maksud Anda. "
            "Apakah Anda ingin menanyakan tentang cuti, payroll, atau status cuti?"
        )
