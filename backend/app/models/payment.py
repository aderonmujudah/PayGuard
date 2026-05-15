import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class Payment(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "payments"

    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id"))
    initiated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    payment_action: Mapped[str] = mapped_column()  # release|hold|block
    payment_status: Mapped[str] = mapped_column(default="pending")  # pending|success|failed
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    currency_code: Mapped[str] = mapped_column(default="NGN")
    provider_name: Mapped[str] = mapped_column(default="mock_squad")
    squad_transaction_ref: Mapped[str | None] = mapped_column(default=None)
    provider_response: Mapped[dict] = mapped_column(JSONB, default=dict)
