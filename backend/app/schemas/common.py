import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Auth ----
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str


# ---- Vendor ----
class BankAccountOut(ORMModel):
    id: uuid.UUID
    account_number: str
    account_name: str
    bank_code: str
    bank_name: str
    is_primary: bool
    is_verified: bool


class VendorOut(ORMModel):
    id: uuid.UUID
    legal_name: str
    display_name: str
    rc_number: str | None
    tin: str | None
    email: str | None
    phone: str | None
    verification_status: str
    onboarding_status: str
    risk_level: str
    bank_accounts: list[BankAccountOut] = []


# ---- Invoice ----
class LineItemOut(ORMModel):
    id: uuid.UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class InvoiceListItem(ORMModel):
    id: uuid.UUID
    invoice_number: str | None
    vendor_id: uuid.UUID | None
    total_amount: Decimal
    currency_code: str
    status: str
    created_at: datetime


class InvoiceDetail(ORMModel):
    id: uuid.UUID
    vendor_id: uuid.UUID | None
    source_file_name: str
    source_file_url: str
    file_hash: str
    invoice_number: str | None
    invoice_date: date | None
    due_date: date | None
    currency_code: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    beneficiary_account_number: str | None
    beneficiary_account_name: str | None
    beneficiary_bank_code: str | None
    status: str
    ocr_status: str
    ocr_confidence: float
    raw_ocr_text: str
    extraction_engine: str
    extracted_data: dict[str, Any]
    created_at: datetime
    line_items: list[LineItemOut] = []


class InvoiceFieldUpdate(BaseModel):
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    currency_code: str | None = None
    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None
    beneficiary_account_number: str | None = None
    beneficiary_account_name: str | None = None
    beneficiary_bank_code: str | None = None
    vendor_id: uuid.UUID | None = None


# ---- Verification ----
class VerificationCheckOut(ORMModel):
    id: uuid.UUID
    check_type: str
    provider_name: str
    status: str
    request_payload: dict[str, Any]
    response_payload: dict[str, Any]
    normalized_result: dict[str, Any]
    created_at: datetime


# ---- Risk ----
class RiskSignalOut(ORMModel):
    signal_code: str
    signal_label: str
    severity: str
    signal_score: int
    details: dict[str, Any]


class RiskAssessmentOut(ORMModel):
    id: uuid.UUID
    score: int
    verdict: str
    explanation: str
    features: dict[str, Any]
    created_at: datetime
    signals: list[RiskSignalOut] = []


# ---- Payment ----
class PaymentActionRequest(BaseModel):
    action: str  # release|hold|block


class PaymentOut(ORMModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    payment_action: str
    payment_status: str
    amount: Decimal
    currency_code: str
    provider_name: str
    squad_transaction_ref: str | None
    provider_response: dict[str, Any]
    created_at: datetime


# ---- Audit ----
class AuditLogOut(ORMModel):
    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    entity_type: str
    entity_id: str
    action: str
    old_values: dict[str, Any]
    new_values: dict[str, Any]
    audit_metadata: dict[str, Any]
    created_at: datetime


# ---- Dashboard ----
class DashboardSummary(BaseModel):
    invoices_by_status: dict[str, int]
    total_invoices: int
    held: int
    blocked: int
    cleared: int
    in_review: int
    recent_activity: list[AuditLogOut]
