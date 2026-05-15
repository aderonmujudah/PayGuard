import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Payment, User
from app.schemas.common import PaymentActionRequest, PaymentOut
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/{invoice_id}/action", response_model=PaymentOut)
def payment_action(
    invoice_id: uuid.UUID,
    payload: PaymentActionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return payment_service.execute_payment_action(
            db, invoice_id, payload.action, user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[PaymentOut])
def list_payments(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return list(
        db.execute(
            select(Payment).order_by(Payment.created_at.desc())
        ).scalars().all()
    )
