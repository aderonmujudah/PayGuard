import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import Timestamps, UUIDPrimaryKey


class AuditLog(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "audit_logs"

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    entity_type: Mapped[str] = mapped_column(index=True)
    entity_id: Mapped[str] = mapped_column(index=True)
    action: Mapped[str] = mapped_column()
    old_values: Mapped[dict] = mapped_column(JSONB, default=dict)
    new_values: Mapped[dict] = mapped_column(JSONB, default=dict)
    audit_metadata: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
