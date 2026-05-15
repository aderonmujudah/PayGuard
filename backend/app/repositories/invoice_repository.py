import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Invoice


def get(db: Session, invoice_id: uuid.UUID) -> Invoice | None:
    return db.execute(
        select(Invoice)
        .where(Invoice.id == invoice_id)
        .options(selectinload(Invoice.line_items), selectinload(Invoice.vendor))
    ).scalar_one_or_none()


def list_invoices(db: Session, status: str | None = None) -> list[Invoice]:
    stmt = select(Invoice).order_by(Invoice.created_at.desc())
    if status:
        stmt = stmt.where(Invoice.status == status)
    return list(db.execute(stmt).scalars().all())


def list_for_review(db: Session) -> list[Invoice]:
    stmt = (
        select(Invoice)
        .where(Invoice.status.in_(["review", "hold"]))
        .order_by(Invoice.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def count_by_status(db: Session) -> dict[str, int]:
    rows = db.execute(
        select(Invoice.status, func.count()).group_by(Invoice.status)
    ).all()
    return {status: count for status, count in rows}


def find_duplicates_by_number(
    db: Session, vendor_id: uuid.UUID | None, invoice_number: str | None, exclude_id: uuid.UUID
) -> list[Invoice]:
    if not invoice_number or not vendor_id:
        return []
    stmt = select(Invoice).where(
        Invoice.vendor_id == vendor_id,
        Invoice.invoice_number == invoice_number,
        Invoice.id != exclude_id,
    )
    return list(db.execute(stmt).scalars().all())


def find_by_file_hash(
    db: Session, file_hash: str, exclude_id: uuid.UUID
) -> list[Invoice]:
    if not file_hash:
        return []
    stmt = select(Invoice).where(
        Invoice.file_hash == file_hash, Invoice.id != exclude_id
    )
    return list(db.execute(stmt).scalars().all())


def vendor_invoice_history(
    db: Session, vendor_id: uuid.UUID | None, exclude_id: uuid.UUID
) -> list[Invoice]:
    if not vendor_id:
        return []
    stmt = select(Invoice).where(
        Invoice.vendor_id == vendor_id, Invoice.id != exclude_id
    )
    return list(db.execute(stmt).scalars().all())
