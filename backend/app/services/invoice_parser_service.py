"""Orchestrates the extraction pipeline for a stored invoice:
OCR -> extraction engine -> persist fields, line items, vendor link.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Invoice, InvoiceLineItem, Vendor
from app.services import audit_service
from app.services.invoice_extraction_engine import get_extraction_engine
from app.services.ocr_service import run_ocr


def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        return Decimal(0)


def _to_date(value) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _match_or_create_vendor(db: Session, vendor_name: str | None) -> uuid.UUID | None:
    if not vendor_name:
        return None
    name = vendor_name.strip()
    vendor = db.execute(
        select(Vendor).where(func.lower(Vendor.legal_name) == name.lower())
    ).scalar_one_or_none()
    if vendor:
        return vendor.id
    vendor = Vendor(
        legal_name=name,
        display_name=name,
        verification_status="unverified",
        onboarding_status="incomplete",
        risk_level="unknown",
    )
    db.add(vendor)
    db.flush()
    return vendor.id


def run_extraction_pipeline(db: Session, invoice_id: uuid.UUID) -> Invoice:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise ValueError("Invoice not found")

    invoice.status = "extracting"
    db.flush()

    storage_key = invoice.source_file_url.rsplit("/", 1)[-1]
    from app.services.file_storage_service import get_storage

    try:
        data = get_storage().read(storage_key)
    except Exception:
        data = b""

    ocr = run_ocr(invoice.source_file_name, data)
    invoice.raw_ocr_text = ocr["text"]
    invoice.ocr_status = ocr["status"]
    invoice.ocr_confidence = ocr["confidence"]

    engine = get_extraction_engine()
    extracted = engine.extract(text=ocr["text"], ocr_confidence=ocr["confidence"])

    invoice.extraction_engine = extracted.get("engine", "")
    invoice.extracted_data = extracted
    invoice.invoice_number = extracted.get("invoice_number")
    invoice.invoice_date = _to_date(extracted.get("invoice_date"))
    invoice.due_date = _to_date(extracted.get("due_date"))
    invoice.currency_code = extracted.get("currency_code") or "NGN"
    invoice.subtotal = _to_decimal(extracted.get("subtotal"))
    invoice.tax_amount = _to_decimal(extracted.get("tax_amount"))
    invoice.total_amount = _to_decimal(extracted.get("total_amount"))
    invoice.beneficiary_account_number = extracted.get("beneficiary_account_number")
    invoice.beneficiary_account_name = extracted.get("beneficiary_account_name")
    invoice.beneficiary_bank_code = extracted.get("beneficiary_bank_code")

    if invoice.vendor_id is None:
        invoice.vendor_id = _match_or_create_vendor(db, extracted.get("vendor_name"))

    # Replace line items.
    for li in list(invoice.line_items):
        db.delete(li)
    for li in extracted.get("line_items", []):
        db.add(
            InvoiceLineItem(
                invoice_id=invoice.id,
                description=str(li.get("description", "")),
                quantity=_to_decimal(li.get("quantity", 1)),
                unit_price=_to_decimal(li.get("unit_price", 0)),
                line_total=_to_decimal(li.get("line_total", 0)),
            )
        )

    invoice.status = "extracted"
    audit_service.record(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="extraction_completed",
        new_values={
            "engine": invoice.extraction_engine,
            "ocr_status": invoice.ocr_status,
            "ocr_confidence": invoice.ocr_confidence,
        },
    )
    db.commit()
    db.refresh(invoice)
    return invoice
