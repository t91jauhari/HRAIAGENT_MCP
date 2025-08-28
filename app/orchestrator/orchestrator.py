import logging
import uuid
from typing import Dict, Any

from app.intent.detector import IntentDetector
from app.memory.session_store import SessionStore
from app.graph.agent_graph import AgentGraphWorkflow, AgentState

logger = logging.getLogger("app.orchestrator.graph_orchestrator")


class AgentOrchestrator:
    """
    Public API for the Agent.
    Wraps the LangGraph workflow and exposes a clean handle_message() method.
    """

    def __init__(self):
        # One detector, one memory store for the orchestrator lifetime
        self.detector = IntentDetector()
        self.memory = SessionStore()
        self.workflow = AgentGraphWorkflow(self.detector, self.memory)

    async def handle_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        trace_id = str(uuid.uuid4())
        logger.info(f"[TRACE:{trace_id}] Orchestrator received message for session {session_id}")

        # Ensure session exists
        self.memory.get(session_id)

        initial_state: AgentState = {
            "trace_id": trace_id,
            "session_id": session_id,
            "user_message": user_message,
            "intents": [],
            "clarifications": [],
            "results": {},
            "assistant_response": "",
            "history": {},
        }

        # Run the LangGraph workflow
        final_state = await self.workflow.graph.ainvoke(initial_state)

        # Always return enriched state (including full session history)
        final_state["history"] = self.memory.full_history(session_id)
        return final_state
