import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def record(
    db: Session,
    *,
    entity_type: str,
    entity_id: str | uuid.UUID,
    action: str,
    actor_user_id: uuid.UUID | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    log = AuditLog(
        actor_user_id=actor_user_id,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        old_values=_jsonable(old_values or {}),
        new_values=_jsonable(new_values or {}),
        audit_metadata=_jsonable(metadata or {}),
    )
    db.add(log)
    db.flush()
    return log


def list_logs(
    db: Session, entity_type: str | None = None, entity_id: str | None = None
) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    return list(db.execute(stmt.limit(200)).scalars().all())
