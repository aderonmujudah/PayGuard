import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models import Invoice, RiskAssessment, User, VerificationCheck
from app.repositories import invoice_repository
from app.schemas.common import (
    InvoiceDetail,
    InvoiceFieldUpdate,
    InvoiceListItem,
    RiskAssessmentOut,
    VerificationCheckOut,
)
from app.services import audit_service
from app.services.file_storage_service import compute_file_hash, get_storage
from app.workers.jobs import enqueue_extraction

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/upload", response_model=InvoiceDetail)
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    file_url = get_storage().save(file.filename or "invoice", data)
    invoice = Invoice(
        uploaded_by=user.id,
        source_file_name=file.filename or "invoice",
        source_file_url=file_url,
        file_hash=compute_file_hash(data),
        status="uploaded",
    )
    db.add(invoice)
    db.flush()
    audit_service.record(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="uploaded",
        actor_user_id=user.id,
        new_values={"file": invoice.source_file_name},
    )
    db.commit()
    db.refresh(invoice)

    enqueue_extraction(invoice.id)
    return invoice_repository.get(db, invoice.id)


@router.get("", response_model=list[InvoiceListItem])
def list_invoices(
    status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return invoice_repository.list_invoices(db, status)


@router.get("/review-queue", response_model=list[InvoiceListItem])
def review_queue(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return invoice_repository.list_for_review(db)


@router.get("/{invoice_id}", response_model=InvoiceDetail)
def get_invoice(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    invoice = invoice_repository.get(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/{invoice_id}/extraction-status")
def extraction_status(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "invoice_id": str(invoice.id),
        "status": invoice.status,
        "ocr_status": invoice.ocr_status,
        "ocr_confidence": invoice.ocr_confidence,
        "extraction_engine": invoice.extraction_engine,
    }


@router.patch("/{invoice_id}", response_model=InvoiceDetail)
def update_fields(
    invoice_id: uuid.UUID,
    payload: InvoiceFieldUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    changes = payload.model_dump(exclude_unset=True)
    old = {k: getattr(invoice, k) for k in changes}
    for k, v in changes.items():
        setattr(invoice, k, v)
    audit_service.record(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="fields_updated",
        actor_user_id=user.id,
        old_values={k: str(v) for k, v in old.items()},
        new_values={k: str(v) for k, v in changes.items()},
    )
    db.commit()
    return invoice_repository.get(db, invoice_id)


@router.get(
    "/{invoice_id}/verification-checks", response_model=list[VerificationCheckOut]
)
def get_checks(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list(
        db.execute(
            select(VerificationCheck)
            .where(VerificationCheck.invoice_id == invoice_id)
            .order_by(VerificationCheck.created_at.desc())
        ).scalars().all()
    )


@router.get("/{invoice_id}/risk", response_model=RiskAssessmentOut)
def get_risk(
    invoice_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    assessment = db.execute(
        select(RiskAssessment)
        .where(RiskAssessment.invoice_id == invoice_id)
        .order_by(RiskAssessment.created_at.desc())
    ).scalars().first()
    if not assessment:
        raise HTTPException(status_code=404, detail="No risk assessment yet")
    return assessment
