from typing import Optional, Literal, List
from pydantic import BaseModel, Field
from datetime import date

# ============================================================
# Employee Profile
# ============================================================

class EmployeeProfileInput(BaseModel):
    employee_id: str = Field(..., description="Employee unique ID (e.g., E-001)")

class EmployeeProfileOutput(BaseModel):
    employee_id: str
    name: str
    department: str
    manager: str
    join_date: date


# ============================================================
# Leave Management
# ============================================================

LeaveType = Literal["annual", "sick", "unpaid", "maternity", "other"]

class LeaveRequestInput(BaseModel):
    employee_id: str = Field(..., description="Employee unique ID")
    start: date
    end: date
    leave_type: LeaveType = Field(default="annual")
    reason: Optional[str] = None

class LeaveRequestOutput(BaseModel):
    request_id: str
    status: Literal["submitted", "needs_approval", "approved", "rejected", "cancelled"]
    message: str

class LeaveBalanceInput(BaseModel):
    employee_id: str = Field(..., description="Employee unique ID")

class LeaveBalanceItem(BaseModel):
    type: LeaveType
    remaining_days: int

class LeaveBalanceOutput(BaseModel):
    employee_id: str
    balances: List[LeaveBalanceItem]

class LeaveStatusInput(BaseModel):
    employee_id: str

class LeaveRecord(BaseModel):
    start: date
    end: date
    type: LeaveType
    approved: bool

class LeaveStatusOutput(BaseModel):
    employee_id: str
    records: List[LeaveRecord]

class LeaveCancelInput(BaseModel):
    employee_id: str
    request_id: str

class LeaveCancelOutput(BaseModel):
    employee_id: str
    request_id: str
    status: Literal["cancelled", "not_found", "error"]


# ============================================================
# Payroll
# ============================================================

class PayrollLookupInput(BaseModel):
    employee_id: str
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

class PayrollHistoryInput(BaseModel):
    employee_id: str
    start_period: Optional[str] = None
    end_period: Optional[str] = None

class PayrollHistoryItem(BaseModel):
    period: str
    net: float

class PayrollHistoryOutput(BaseModel):
    employee_id: str
    history: List[PayrollHistoryItem]

class DeductionReasonInput(BaseModel):
    employee_id: str
    period: str

class DeductionReasonOutput(BaseModel):
    employee_id: str
    period: str
    reason: str


# ============================================================
# Attendance
# ============================================================

class AttendanceCheckInput(BaseModel):
    employee_id: str
    period: Optional[str] = None

class AttendanceAnomaly(BaseModel):
    date: date
    status: Literal["absent", "late", "present"]
    note: Optional[str] = None

class AttendanceCheckOutput(BaseModel):
    employee_id: str
    period: str
    anomalies: List[AttendanceAnomaly]

class AttendanceSummaryInput(BaseModel):
    employee_id: str
    start_period: Optional[str] = None
    end_period: Optional[str] = None

class AttendanceSummaryOutput(BaseModel):
    employee_id: str
    period_range: str
    present: int
    absent: int
    late: int


# ============================================================
# Benefits
# ============================================================

class BenefitSummaryInput(BaseModel):
    employee_id: str

class BenefitSummaryOutput(BaseModel):
    employee_id: str
    benefits: dict


# ============================================================
# HR Policy
# ============================================================

class HRPolicyInput(BaseModel):
    topic: Optional[str] = None

class HRPolicyOutput(BaseModel):
    topic: str
    policy: str

