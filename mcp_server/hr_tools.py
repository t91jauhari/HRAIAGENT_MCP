import uuid
import logging
import json
from typing import Any
import mcp.types as types

from . import models

logger = logging.getLogger("mcp.hr_tools")


class HRServices:
    def submit_leave(self, inp: models.LeaveRequestInput) -> models.LeaveRequestOutput:
        rid = str(uuid.uuid4())
        logger.info(f"[MCP-TOOLS] Submit leave employee={inp.employee_id}, {inp.start}→{inp.end}")
        return models.LeaveRequestOutput(
            request_id=rid,
            status="needs_approval",
            message=f"Leave request {inp.start} → {inp.end} submitted for {inp.employee_id}",
        )

    def leave_balance(self, inp: models.LeaveBalanceInput) -> models.LeaveBalanceOutput:
        balances = [
            models.LeaveBalanceItem(type="annual", remaining_days=8),
            models.LeaveBalanceItem(type="sick", remaining_days=4),
            models.LeaveBalanceItem(type="maternity", remaining_days=90),
        ]
        return models.LeaveBalanceOutput(
            employee_id=inp.employee_id,
            balances=balances
        )

    def payroll_lookup(self, inp: models.PayrollLookupInput) -> models.PayrollLookupOutput:
        period = inp.period or "2025-08"
        items = [
            models.PayrollItem(code="BASIC", label="Basic Salary", amount=20_000_000.0),
            models.PayrollItem(code="ALLOW", label="Allowance", amount=3_000_000.0),
            models.PayrollItem(code="DEDUCT", label="Deduction (Unpaid leave)", amount=-1_000_000.0),
        ]
        net = sum(i.amount for i in items)
        logger.info(f"[MCP-TOOLS] Payroll lookup employee={inp.employee_id}, period={period}, net={net}")
        return models.PayrollLookupOutput(employee_id=inp.employee_id, period=period, net_pay=net, items=items)

    def deduction_reason(self, inp: models.DeductionReasonInput):
        logger.info(f"[MCP-TOOLS] Deduction reason for {inp.employee_id} period={inp.period}")
        return {
            "employee_id": inp.employee_id,
            "period": inp.period,
            "reason": "Unpaid leave for 3 days in this period"
        }

    def leave_status(self, inp: models.LeaveStatusInput) -> models.LeaveStatusOutput:
        balances = [
            models.LeaveBalanceItem(type="annual", remaining_days=10),
            models.LeaveBalanceItem(type="sick", remaining_days=5),
        ]
        logger.info(f"[MCP-TOOLS] Leave status lookup employee={inp.employee_id}")
        return models.LeaveStatusOutput(employee_id=inp.employee_id, balances=balances)

    def attendance_check(self, inp: models.AttendanceCheckInput):
        logger.info(f"[MCP-TOOLS] Attendance check employee={inp.employee_id}, period={inp.period}")
        return {
            "employee_id": inp.employee_id,
            "period": inp.period,
            "late_days": [
                {"date": "2025-08-18", "minutes_late": 120}
            ]
        }

    def attendance_summary(self, inp: models.AttendanceSummaryInput):
        logger.info(f"[MCP-TOOLS] Attendance summary employee={inp.employee_id}, period={inp.period}")
        return {
            "employee_id": inp.employee_id,
            "period": inp.period,
            "summary": {
                "present": 18,
                "absent": 2,
                "late": 1
            }
        }

    def benefit_summary(self, inp: models.BenefitSummaryInput):
        logger.info(f"[MCP-TOOLS] Benefit summary for {inp.employee_id}")
        return {
            "employee_id": inp.employee_id,
            "benefits": [
                {"code": "HLTH", "label": "Health Insurance", "value": "Active"},
                {"code": "MEAL", "label": "Meal Allowance", "value": "Rp 500,000"}
            ]
        }



services = HRServices()

# 🔑 Central registry: tool name → input model
MODEL_MAP = {
    "leave_request": models.LeaveRequestInput,
    "leave_status": models.LeaveStatusInput,
    "payroll_lookup": models.PayrollLookupInput,
    "payroll_history": models.PayrollHistoryInput,
    "deduction_reason": models.DeductionReasonInput,
    "attendance_check": models.AttendanceCheckInput,
    "attendance_summary": models.AttendanceSummaryInput,
    "leave_balance": models.LeaveBalanceInput,
    "leave_cancel": models.LeaveCancelInput,
    "benefit_summary": models.BenefitSummaryInput,
    "hr_policy": models.HRPolicyInput,
    "employee_profile": models.EmployeeProfileInput,
}


# ---- Dispatcher ----
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    if not hasattr(services, name):
        raise ValueError(f"Unknown tool: {name}")

    input_cls = MODEL_MAP.get(name)
    if input_cls:
        inp = input_cls(**arguments)  # ✅ Always validated Pydantic model
    else:
        inp = arguments

    result = getattr(services, name)(inp)

    # ✅ Normalize output to dict
    if hasattr(result, "model_dump"):  # Pydantic v2
        payload = result.model_dump()
    elif hasattr(result, "dict"):  # Pydantic v1 fallback
        payload = result.dict()
    else:
        payload = result

    return [types.TextContent(type="text", text=json.dumps(payload))]

# ---- Tool Registry ----
async def list_tools() -> list[types.Tool]:
    tools = []
    for name, input_cls in MODEL_MAP.items():
        tools.append(
            types.Tool(
                name=name,
                title=name.replace("_", " ").title(),
                description=f"{name.replace('_', ' ').capitalize()} tool",
                inputSchema=input_cls.model_json_schema()
            )
        )
    return tools

