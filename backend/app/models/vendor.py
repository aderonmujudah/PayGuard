import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class Vendor(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "vendors"

    legal_name: Mapped[str] = mapped_column(index=True)
    display_name: Mapped[str] = mapped_column(default="")
    rc_number: Mapped[str | None] = mapped_column(default=None)
    tin: Mapped[str | None] = mapped_column(default=None)
    email: Mapped[str | None] = mapped_column(default=None)
    phone: Mapped[str | None] = mapped_column(default=None)
    verification_status: Mapped[str] = mapped_column(default="unverified")  # unverified|pending|verified|failed
    onboarding_status: Mapped[str] = mapped_column(default="new")  # new|incomplete|complete
    risk_level: Mapped[str] = mapped_column(default="unknown")  # low|medium|high|unknown

    bank_accounts: Mapped[list["VendorBankAccount"]] = relationship(
        back_populates="vendor", cascade="all, delete-orphan"
    )
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="vendor")  # noqa: F821


class VendorBankAccount(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "vendor_bank_accounts"

    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"))
    account_number: Mapped[str] = mapped_column(index=True)
    account_name: Mapped[str] = mapped_column(default="")
    bank_code: Mapped[str] = mapped_column(default="")
    bank_name: Mapped[str] = mapped_column(default="")
    is_primary: Mapped[bool] = mapped_column(default=False)
    is_verified: Mapped[bool] = mapped_column(default=False)

    vendor: Mapped[Vendor] = relationship(back_populates="bank_accounts")
