from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.repositories import invoice_repository
from app.schemas.common import DashboardSummary
from app.services import audit_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    by_status = invoice_repository.count_by_status(db)
    return DashboardSummary(
        invoices_by_status=by_status,
        total_invoices=sum(by_status.values()),
        held=by_status.get("hold", 0),
        blocked=by_status.get("blocked", 0),
        cleared=by_status.get("cleared", 0),
        in_review=by_status.get("review", 0),
        recent_activity=audit_service.list_logs(db)[:15],
    )
