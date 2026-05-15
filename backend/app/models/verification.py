import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class VerificationCheck(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "verification_checks"

    invoice_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("invoices.id"))
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendors.id"))
    check_type: Mapped[str] = mapped_column()  # account_verification|business_verification
    provider_name: Mapped[str] = mapped_column(default="")
    status: Mapped[str] = mapped_column(default="pending")  # pending|passed|failed|error
    request_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    response_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    normalized_result: Mapped[dict] = mapped_column(JSONB, default=dict)
