from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.common import AuditLogOut
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogOut])
def list_audit(
    entity_type: str | None = None,
    entity_id: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return audit_service.list_logs(db, entity_type, entity_id)
