import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.common import InvoiceDetail, RiskAssessmentOut, VerificationCheckOut
from app.services import (
    invoice_parser_service,
    risk_engine_service,
    vendor_verification_service,
)
from app.repositories import invoice_repository

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/{invoice_id}/extract", response_model=InvoiceDetail)
def run_extraction(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        invoice_parser_service.run_extraction_pipeline(db, invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return invoice_repository.get(db, invoice_id)


@router.post(
    "/{invoice_id}/verify", response_model=list[VerificationCheckOut]
)
def run_verification(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return vendor_verification_service.run_verification_checks(db, invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{invoice_id}/assess", response_model=RiskAssessmentOut)
def run_assessment(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    try:
        return risk_engine_service.run_risk_assessment(db, invoice_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
