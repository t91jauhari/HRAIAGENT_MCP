from typing import Optional, Literal, List
from pydantic import BaseModel, Field
from datetime import date


# ---- Leave Request ----
LeaveType = Literal["annual", "sick", "unpaid", "maternity", "other"]

class LeaveRequestInput(BaseModel):
    employee_id: str = Field(..., description="Employee unique ID (e.g., E-001)")
    start: date = Field(..., description="Leave start date (YYYY-MM-DD)")
    end: date = Field(..., description="Leave end date (YYYY-MM-DD)")
    leave_type: LeaveType = Field(default="annual")
    reason: Optional[str] = Field(default=None)


class LeaveRequestOutput(BaseModel):
    request_id: str
    status: Literal["submitted", "needs_approval", "rejected", "error"]
    message: str


# ---- Payroll Lookup ----
class PayrollLookupInput(BaseModel):
    employee_id: str = Field(..., description="Employee unique ID (e.g., E-001)")
    period: Optional[str] = Field(None, description="Payroll period (YYYY-MM or 'latest')")


class PayrollItem(BaseModel):
    code: str
    label: str
    amount: float


class PayrollLookupOutput(BaseModel):
    employee_id: str
    period: str
    net_pay: float
    items: List[PayrollItem]


# ---- Leave Status ----
class LeaveStatusInput(BaseModel):
    employee_id: str = Field(..., description="Employee unique ID (e.g., E-001)")


class LeaveBalance(BaseModel):
    type: LeaveType
    remaining_days: int


class LeaveStatusOutput(BaseModel):
    employee_id: str
    balances: List[LeaveBalance]
