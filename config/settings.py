import os
from pydantic import BaseSettings
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


class Settings(BaseSettings):
    """
    Centralized application settings.
    Loads from environment variables or .env file.
    """

    # Hugging Face API
    hf_api_key: str = os.getenv("HF_API_KEY", "")
    hf_model: str = os.getenv("HF_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")

    # MCP
    mcp_mode: str = os.getenv("MCP_MODE", "stdio")
    mcp_host: str = os.getenv("MCP_HOST", "0.0.0.0")
    mcp_port: int = int(os.getenv("MCP_PORT", 8001))

    # App
    app_name: str = "HR-AI MCP Backend"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
