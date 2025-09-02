import logging
import uuid
from typing import Dict, Any
from app.planner.plan_generator import PlanGenerator
from app.planner.plan_executor import PlanExecutor
from app.planner.reflection_engine import ReflectionEngine
from app.planner.response_builder import ResponseBuilder

logger = logging.getLogger("autonomous.orchestrator")


class AutonomousChatOrchestrator:
    """
    End-to-end orchestrator for autonomous HR chat.
    Coordinates planning, execution, reflection, and response building.
    """

    def __init__(self):
        self.plan_generator = PlanGenerator()
        self.plan_executor = PlanExecutor()
        self.reflection_engine = ReflectionEngine()
        self.response_builder = ResponseBuilder()

    async def handle_message(self, user_message: str) -> Dict[str, Any]:
        # Generate session ID
        session_id = str(uuid.uuid4())
        trace = lambda stage, msg: logger.info(f"[TRACE][{session_id}][{stage}] {msg}")

        trace("START", f"Received message: {user_message!r}")

        # Step 1: Planning
        plan = await self.plan_generator.generate_plan(user_message)
        trace("PLAN", f"Generated plan: {plan}")

        # Step 2: Execution
        results = await self.plan_executor.execute(plan)
        trace("EXEC", f"Execution results: {results}")

        # Step 3: Reflection
        reflection = self.reflection_engine.reflect(user_message, results)
        trace("REFLECT", f"Reflection output: {reflection!r}")

        # Step 4: Response building
        response = self.response_builder.build(user_message, results, reflection)
        trace("RESP", f"Final response: {response!r}")

        trace("END", "Pipeline completed.")

        return {
            "session_id": session_id,
            "user_message": user_message,
            "plan": plan,
            "results": results,
            "reflection": reflection,
            "response": response
        }
