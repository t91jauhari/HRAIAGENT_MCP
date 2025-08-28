import datetime
import uuid
from typing import Dict, Any, List


class SessionStore:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "session_id": session_id,
                "created_at": datetime.datetime.utcnow().isoformat(),
                "messages": [],
                "intents": [],
                "tool_calls": [],
                "clarifications": [],
                "state": {
                    "active_intent": None,
                    "status": "idle",           # idle | awaiting_args | executing | completed
                    "last_completed": False,
                    "pending_args": [],
                    "provided_args": {},
                    "context_stack": [],
                    "last_intent_type": None,
                    "last_user_action": None,
                    "timestamp": datetime.datetime.utcnow().isoformat()
                }
            }
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        session = self.get(session_id)
        entry = {
            "id": str(uuid.uuid4()),
            "time": datetime.datetime.utcnow().isoformat(),
            "role": role,
            "content": content,
            "state": session["state"].copy()   # snapshot state at this turn
        }
        session["messages"].append(entry)

    def add_intents(self, session_id: str, intents: List[Dict[str, Any]]):
        self.get(session_id)["intents"].append({
            "id": str(uuid.uuid4()),
            "time": datetime.datetime.utcnow().isoformat(),
            "intents": intents,
            "state": self.get(session_id)["state"].copy()
        })

    def add_tool_call(self, session_id: str, tool: str, args: Dict[str, Any], result: Any):
        self.get(session_id)["tool_calls"].append({
            "id": str(uuid.uuid4()),
            "time": datetime.datetime.utcnow().isoformat(),
            "tool": tool,
            "args": args,
            "result": result,
            "state": self.get(session_id)["state"].copy()
        })

    def add_clarification(self, session_id: str, intent: str, missing: List[str]):
        self.get(session_id)["clarifications"].append({
            "id": str(uuid.uuid4()),
            "time": datetime.datetime.utcnow().isoformat(),
            "intent": intent,
            "missing": missing,
            "state": self.get(session_id)["state"].copy()
        })

    # ---- NEW conversation state helpers ----
    def set_state(self, session_id: str,
                  active_intent: str = None,
                  status: str = None,
                  pending_args: List[str] = None,
                  provided_args: Dict[str, Any] = None,
                  last_completed: bool = None,
                  last_intent_type: str = None,
                  last_user_action: str = None):
        session = self.get(session_id)
        state = session["state"]

        # merge instead of overwrite
        if active_intent is not None:
            state["active_intent"] = active_intent
        if status is not None:
            state["status"] = status
        if pending_args is not None:
            state["pending_args"] = pending_args
        if provided_args is not None:
            state["provided_args"].update(provided_args)
        if last_completed is not None:
            state["last_completed"] = last_completed
        if last_intent_type is not None:
            state["last_intent_type"] = last_intent_type
        if last_user_action is not None:
            state["last_user_action"] = last_user_action

        state["timestamp"] = datetime.datetime.utcnow().isoformat()

    def get_state(self, session_id: str) -> Dict[str, Any]:
        return self.get(session_id)["state"]

    def reset_state(self, session_id: str):
        session = self.get(session_id)
        session["state"] = {
            "active_intent": None,
            "status": "idle",
            "last_completed": False,
            "pending_args": [],
            "provided_args": {},
            "context_stack": [],
            "last_intent_type": None,
            "last_user_action": None,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    def push_context(self, session_id: str, intent: str):
        session = self.get(session_id)
        session["state"]["context_stack"].append(intent)

    def pop_context(self, session_id: str) -> str:
        session = self.get(session_id)
        if session["state"]["context_stack"]:
            return session["state"]["context_stack"].pop()
        return None

    def clear_last_completed(self, session_id: str):
        self.get(session_id)["state"]["last_completed"] = False

    def set_last_completed(self, session_id: str):
        self.get(session_id)["state"]["last_completed"] = True

    def full_history(self, session_id: str) -> Dict[str, Any]:
        return self.get(session_id)
