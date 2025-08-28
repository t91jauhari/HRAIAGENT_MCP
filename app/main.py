import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.orchestrator.orchestrator import AgentOrchestrator

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.main")

# Initialize FastAPI app
app = FastAPI(title="HR-AI MCP Backend", version="1.0.0")

# Initialize Agent
agent = AgentOrchestrator()

# ---- Request / Response Models ----
class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    trace_id: str
    session_id: str
    intents: list
    results: dict
    clarifications: list
    assistant_response: str
    history: dict


# ---- Routes ----
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Main chat endpoint.
    Accepts a session_id and user message,
    returns structured response + chatbot reply.
    """
    try:
        result = await agent.handle_message(req.session_id, req.message)
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"[CHAT-ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "HR-AI MCP Backend"}
