import logging
from typing import TypedDict, Dict, Any, List
from langgraph.graph import StateGraph, END

from app.intent.detector import IntentDetector
from app.memory.session_store import SessionStore
from app.graph.multi_intent_planner import execute_intents
from app.graph.clarifier import get_missing_args
from app.graph.response_builder import ResponseBuilder

logger = logging.getLogger("app.graph.agent_graph")


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

    async def _detect_intent_node(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        user_message = state["user_message"]
        trace_id = state["trace_id"]

        session = self.memory.get(session_id)
        memory_summary = self._summarize_memory(session)
        conversation_state = self.memory.get_state(session_id)

        detection = await self.detector.detect(user_message, memory_summary)
        intents = detection.get("intents", [])

        self.memory.add_message(session_id, "user", user_message)
        self.memory.add_intents(session_id, intents)

        logger.info(f"[TRACE:{trace_id}] Detected intents={intents}, prev_state={conversation_state}")

        # Chit-chat override (if only null args HR intents detected)
        is_chitchat = (
            not intents
            or all(i.get("confidence", 0) < 0.7 for i in intents)
            or all(not any(v for v in (i.get("args") or {}).values()) for i in intents)
        )

        if conversation_state["status"] == "awaiting_args" and is_chitchat:
            logger.info(f"[TRACE:{trace_id}] Chit-chat while awaiting args, keeping pending flow alive.")
            self.memory.set_state(session_id, last_intent_type="chit_chat")
            state["results"] = {"fallback": {"status": "no_intent"}}
            state["intents"] = []
            return state

        # Resume unfinished flow if new args provided
        if conversation_state["status"] == "awaiting_args" and intents:
            active_intent = conversation_state["active_intent"]
            provided_args = intents[0].get("args", {})
            if any(v not in (None, "") for v in provided_args.values()):
                logger.info(f"[TRACE:{trace_id}] Resuming intent {active_intent} with new args")
                self.memory.set_state(session_id, active_intent, "executing", provided_args=provided_args)
            else:
                state["results"] = {"fallback": {"status": "no_intent"}}
                state["intents"] = []
                return state

        # Fresh HR intent
        elif intents:
            missing_args = await get_missing_args(intents[0]["name"], intents[0].get("args", {}))
            if missing_args:
                self.memory.set_state(session_id, intents[0]["name"], "awaiting_args", pending_args=missing_args)
            else:
                self.memory.set_state(session_id, intents[0]["name"], "executing")

        # Pure chit-chat
        else:
            state["results"] = {"fallback": {"status": "no_intent"}}
            self.memory.set_state(session_id, None, "idle", last_intent_type="chit_chat")

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
                self.memory.set_state(session_id, intent["name"], "awaiting_args", pending_args=missing)
                clarifications.append({"intent": intent["name"], "missing": missing})

        state["clarifications"] = clarifications
        if clarifications:
            logger.warning(f"[TRACE:{trace_id}] Clarifications required={clarifications}")
        return state

    async def _execute_node(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        intents = state["intents"]
        clarifications = state["clarifications"]
        trace_id = state["trace_id"]

        results = state.get("results", {})
        if not clarifications and intents:
            self.memory.set_state(session_id, intents[0]["name"], "executing")
            results = await execute_intents(intents, self.memory, session_id)
            self.memory.set_state(session_id, intents[0]["name"], "completed")

        logger.info(f"[TRACE:{trace_id}] Execution results={results}")
        state["results"] = results
        return state

    def _respond_node(self, state: AgentState) -> AgentState:
        session_id = state["session_id"]
        results = state.get("results", {})
        clarifications = state.get("clarifications", [])
        trace_id = state["trace_id"]
        user_message = state.get("user_message", "")

        # Fetch conversation state before building response
        conv_state = self.memory.get_state(session_id)

        # Pass conversation state into ResponseBuilder
        assistant_response = self.response_builder.build(
            results, clarifications, user_message, state=conv_state
        )
        self.memory.add_message(session_id, "assistant", assistant_response)

        # Reset if flow is fully completed
        if conv_state["status"] == "completed":
            logger.info(f"[TRACE:{trace_id}] Resetting state after completion")
            self.memory.reset_state(session_id)
            self.memory.set_last_completed(session_id)

        state["assistant_response"] = assistant_response
        state["history"] = self.memory.full_history(session_id)

        logger.info(f"[TRACE:{trace_id}] Assistant response={assistant_response}")
        return state

    def _summarize_memory(self, session: Dict[str, Any]) -> str:
        msgs = [f"{m['role']}: {m['content']}" for m in session["messages"][-5:]]
        return "\n".join(msgs)
