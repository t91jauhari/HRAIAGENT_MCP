import logging
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END

from app.intent.detector import IntentDetector
from app.memory.session_store import SessionStore
from app.graph.multi_intent_planner import execute_intents
from app.graph.clarifier import get_missing_args
from app.graph.response_builder import ResponseBuilder

logger = logging.getLogger("app.graph.agent_graph")


# ---- LangGraph State ----
class AgentState(TypedDict):
    trace_id: str
    session_id: str
    user_message: str
    intents: List[Dict[str, Any]]
    clarifications: List[Dict[str, Any]]
    results: Dict[str, Any]
    assistant_response: str
    history: Dict[str, Any]


class AgentGraphWorkflow:
    """
    Defines the LangGraph workflow for the agent:
    detect_intent → clarify → execute → respond
    """

    def __init__(self, detector: IntentDetector, memory: SessionStore):
        self.detector = detector
        self.memory = memory
        self.response_builder = ResponseBuilder()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("detect_intent", self._detect_intent_node)
        workflow.add_node("clarify", self._clarify_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("respond", self._respond_node)

        workflow.set_entry_point("detect_intent")
        workflow.add_edge("detect_intent", "clarify")
        workflow.add_edge("clarify", "execute")
        workflow.add_edge("execute", "respond")
        workflow.add_edge("respond", END)

        return workflow.compile()

    # ---- Node implementations ----

    async def _detect_intent_node(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        user_message = state["user_message"]
        trace_id = state["trace_id"]

        session = self.memory.get(session_id)
        memory_summary = self._summarize_memory(session)

        detection = await self.detector.detect(user_message, memory_summary)
        intents = detection.get("intents", [])

        self.memory.add_message(session_id, "user", user_message)
        self.memory.add_intents(session_id, intents)

        logger.info(f"[TRACE:{trace_id}] Detected intents={intents}")

        if not intents:
            state["results"] = {"fallback": {"status": "no_intent"}}

        state["intents"] = intents
        return state

    async def _clarify_node(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        intents = state["intents"]
        trace_id = state["trace_id"]

        clarifications = []
        for intent in intents:
            missing = await get_missing_args(intent["name"], intent.get("args", {}))
            if missing:
                self.memory.add_clarification(session_id, intent["name"], missing)
                clarifications.append({"intent": intent["name"], "missing": missing})

        if clarifications:
            logger.warning(f"[TRACE:{trace_id}] Clarifications required={clarifications}")

        state["clarifications"] = clarifications
        return state

    async def _execute_node(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        intents = state["intents"]
        clarifications = state["clarifications"]
        trace_id = state["trace_id"]

        results = state.get("results", {})  # preserve fallback if already set
        if not clarifications and intents:
            results = await execute_intents(intents, self.memory, session_id)

        logger.info(f"[TRACE:{trace_id}] Execution results={results}")
        state["results"] = results
        return state

    def _respond_node(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        results = state.get("results", {})
        clarifications = state.get("clarifications", [])
        trace_id = state["trace_id"]
        user_message = state.get("user_message", "")

        # Pass user_message into ResponseBuilder
        assistant_response = self.response_builder.build(
            results, clarifications, user_message
        )
        self.memory.add_message(session_id, "assistant", assistant_response)

        state["assistant_response"] = assistant_response
        state["history"] = self.memory.full_history(session_id)

        logger.info(f"[TRACE:{trace_id}] Assistant response={assistant_response}")
        return state

    def _summarize_memory(self, session: Dict[str, Any]) -> str:
        msgs = [f"{m['role']}: {m['content']}" for m in session["messages"][-5:]]
        return "\n".join(msgs)
