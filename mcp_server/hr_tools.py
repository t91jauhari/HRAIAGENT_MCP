import uuid
import logging
import json
from typing import Any
import mcp.types as types

from .models import (
    LeaveRequestInput, LeaveRequestOutput,
    PayrollLookupInput, PayrollLookupOutput, PayrollItem,
    LeaveStatusInput, LeaveStatusOutput, LeaveBalance,
)

logger = logging.getLogger("mcp.hr_tools")


class HRServices:
    def submit_leave(self, inp: LeaveRequestInput) -> LeaveRequestOutput:
        rid = str(uuid.uuid4())
        logger.info(f"[MCP-TOOLS] Submit leave employee={inp.employee_id}, {inp.start}→{inp.end}")
        return LeaveRequestOutput(
            request_id=rid,
            status="needs_approval",
            message=f"Leave request {inp.start} → {inp.end} submitted for {inp.employee_id}",
        )

    def payroll_lookup(self, inp: PayrollLookupInput) -> PayrollLookupOutput:
        period = inp.period or "2025-08"
        items = [
            PayrollItem(code="BASIC", label="Basic Salary", amount=20_000_000.0),
            PayrollItem(code="ALLOW", label="Allowance", amount=3_000_000.0),
            PayrollItem(code="DEDUCT", label="Deduction", amount=-1_000_000.0),
        ]
        net = sum(i.amount for i in items)
        logger.info(f"[MCP-TOOLS] Payroll lookup employee={inp.employee_id}, period={period}, net={net}")
        return PayrollLookupOutput(employee_id=inp.employee_id, period=period, net_pay=net, items=items)

    def leave_status(self, inp: LeaveStatusInput) -> LeaveStatusOutput:
        balances = [
            LeaveBalance(type="annual", remaining_days=10),
            LeaveBalance(type="sick", remaining_days=5),
        ]
        logger.info(f"[MCP-TOOLS] Leave status lookup employee={inp.employee_id}")
        return LeaveStatusOutput(employee_id=inp.employee_id, balances=balances)


services = HRServices()


# ---- Dispatcher ----
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
    if name == "leave_request":
        result = services.submit_leave(LeaveRequestInput(**arguments))
        return [types.TextContent(type="text", text=json.dumps(result.model_dump()))]

    if name == "payroll_lookup":
        result = services.payroll_lookup(PayrollLookupInput(**arguments))
        return [types.TextContent(type="text", text=json.dumps(result.model_dump()))]

    if name == "leave_status":
        result = services.leave_status(LeaveStatusInput(**arguments))
        return [types.TextContent(type="text", text=json.dumps(result.model_dump()))]

    raise ValueError(f"Unknown tool: {name}")


# ---- Tool Registry ----
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="leave_request",
            title="Submit Leave Request",
            description="Submit a leave request for an employee",
            inputSchema=LeaveRequestInput.model_json_schema()
        ),
        types.Tool(
            name="payroll_lookup",
            title="Payroll Lookup",
            description="Lookup payroll details for an employee in a period",
            inputSchema=PayrollLookupInput.model_json_schema()
        ),
        types.Tool(
            name="leave_status",
            title="Leave Status",
            description="Check leave balances for an employee",
            inputSchema=LeaveStatusInput.model_json_schema()
        ),
    ]
