import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Vendor


def get(db: Session, vendor_id: uuid.UUID) -> Vendor | None:
    return db.execute(
        select(Vendor)
        .where(Vendor.id == vendor_id)
        .options(selectinload(Vendor.bank_accounts))
    ).scalar_one_or_none()


def list_vendors(db: Session) -> list[Vendor]:
    return list(
        db.execute(select(Vendor).order_by(Vendor.legal_name)).scalars().all()
    )
