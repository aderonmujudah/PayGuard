import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class Invoice(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "invoices"

    vendor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("vendors.id"))
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    source_file_name: Mapped[str] = mapped_column(default="")
    source_file_url: Mapped[str] = mapped_column(default="")
    file_hash: Mapped[str] = mapped_column(index=True, default="")

    invoice_number: Mapped[str | None] = mapped_column(index=True, default=None)
    invoice_date: Mapped[date | None] = mapped_column(default=None)
    due_date: Mapped[date | None] = mapped_column(default=None)
    currency_code: Mapped[str] = mapped_column(default="NGN")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    beneficiary_account_number: Mapped[str | None] = mapped_column(default=None)
    beneficiary_account_name: Mapped[str | None] = mapped_column(default=None)
    beneficiary_bank_code: Mapped[str | None] = mapped_column(default=None)

    status: Mapped[str] = mapped_column(default="uploaded", index=True)
    # uploaded|extracting|extracted|verifying|verified|assessed|cleared|review|hold|blocked|failed
    ocr_status: Mapped[str] = mapped_column(default="pending")  # pending|done|skipped|failed
    ocr_confidence: Mapped[float] = mapped_column(default=0.0)
    raw_ocr_text: Mapped[str] = mapped_column(default="")
    extraction_engine: Mapped[str] = mapped_column(default="")
    extracted_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    vendor = relationship("Vendor", back_populates="invoices")
    line_items: Mapped[list["InvoiceLineItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )


class InvoiceLineItem(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "invoice_line_items"

    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id"))
    description: Mapped[str] = mapped_column(default="")
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    invoice: Mapped[Invoice] = relationship(back_populates="line_items")
