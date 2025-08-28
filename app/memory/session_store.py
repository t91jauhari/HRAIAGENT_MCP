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
                "clarifications": []
            }
        return self.sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str):
        self.get(session_id)["messages"].append({
            "id": str(uuid.uuid4()),
            "time": datetime.datetime.utcnow().isoformat(),
            "role": role,
            "content": content,
        })

    def add_intents(self, session_id: str, intents: List[Dict[str, Any]]):
        self.get(session_id)["intents"].append({
            "id": str(uuid.uuid4()),
            "time": datetime.datetime.utcnow().isoformat(),
            "intents": intents,
        })

    def add_tool_call(self, session_id: str, tool: str, args: Dict[str, Any], result: Any):
        self.get(session_id)["tool_calls"].append({
            "id": str(uuid.uuid4()),
            "time": datetime.datetime.utcnow().isoformat(),
            "tool": tool,
            "args": args,
            "result": result,
        })

    def add_clarification(self, session_id: str, intent: str, missing: List[str]):
        self.get(session_id)["clarifications"].append({
            "id": str(uuid.uuid4()),
            "time": datetime.datetime.utcnow().isoformat(),
            "intent": intent,
            "missing": missing,
        })

    def full_history(self, session_id: str) -> Dict[str, Any]:
        return self.get(session_id)
