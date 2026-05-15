import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class RiskAssessment(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "risk_assessments"

    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id"))
    score: Mapped[int] = mapped_column(default=0)
    verdict: Mapped[str] = mapped_column(default="CLEAR")  # CLEAR|REVIEW|HOLD|BLOCK
    explanation: Mapped[str] = mapped_column(default="")
    features: Mapped[dict] = mapped_column(JSONB, default=dict)

    signals: Mapped[list["RiskSignal"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class RiskSignal(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "risk_signals"

    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("risk_assessments.id"))
    signal_code: Mapped[str] = mapped_column()
    signal_label: Mapped[str] = mapped_column()
    severity: Mapped[str] = mapped_column(default="low")  # low|medium|high
    signal_score: Mapped[int] = mapped_column(default=0)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)

    assessment: Mapped[RiskAssessment] = relationship(back_populates="signals")
