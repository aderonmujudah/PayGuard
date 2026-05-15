import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Invoice, User, VerificationCheck
from app.repositories import vendor_repository
from app.schemas.common import (
    InvoiceListItem,
    VendorOut,
    VerificationCheckOut,
)

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.get("", response_model=list[VendorOut])
def list_vendors(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return vendor_repository.list_vendors(db)


@router.get("/{vendor_id}", response_model=VendorOut)
def get_vendor(
    vendor_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    vendor = vendor_repository.get(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.get("/{vendor_id}/invoices", response_model=list[InvoiceListItem])
def vendor_invoices(
    vendor_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list(
        db.execute(
            select(Invoice)
            .where(Invoice.vendor_id == vendor_id)
            .order_by(Invoice.created_at.desc())
        ).scalars().all()
    )


@router.get(
    "/{vendor_id}/verification-history", response_model=list[VerificationCheckOut]
)
def vendor_verification_history(
    vendor_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list(
        db.execute(
            select(VerificationCheck)
            .where(VerificationCheck.vendor_id == vendor_id)
            .order_by(VerificationCheck.created_at.desc())
        ).scalars().all()
    )
