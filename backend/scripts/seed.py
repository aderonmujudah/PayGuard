"""Seed demo data covering the five risk scenarios.

Run: python -m scripts.seed   (after alembic upgrade head)

Scenarios:
  1. Clean invoice                  -> CLEAR
  2. Duplicate invoice number       -> REVIEW/HOLD
  3. Fake / new unverified vendor   -> REVIEW
  4. Bank account name mismatch     -> HOLD
  5. Inflated amount vs history     -> HOLD/REVIEW
"""

import io
import uuid
from decimal import Decimal

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models import Invoice, User, Vendor, VendorBankAccount
from app.services import (
    invoice_parser_service,
    risk_engine_service,
    vendor_verification_service,
)
from app.services.file_storage_service import compute_file_hash, get_storage


def _invoice_text(**kw) -> str:
    return f"""INVOICE
Vendor: {kw['vendor']}
Invoice Number: {kw['number']}
Invoice Date: {kw['date']}
Due Date: {kw['due']}
Account Name: {kw['acct_name']}
Account Number: {kw['acct_no']}
Bank Code: {kw['bank_code']}
Subtotal: {kw['subtotal']}
VAT (7.5%): {kw['tax']}
Grand Total: {kw['total']}
"""


def _store_text_invoice(name: str, text: str) -> tuple[str, str]:
    data = text.encode()
    url = get_storage().save(name, data)
    return url, compute_file_hash(data)


def _make_invoice(db, user, vendor_id, name, text, **fields) -> Invoice:
    url, fhash = _store_text_invoice(name, text)
    inv = Invoice(
        uploaded_by=user.id,
        vendor_id=vendor_id,
        source_file_name=name,
        source_file_url=url,
        file_hash=fields.pop("file_hash", fhash),
        status="uploaded",
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    invoice_parser_service.run_extraction_pipeline(db, inv.id)
    # Apply explicit overrides (extraction from synthetic text is best-effort).
    inv = db.get(Invoice, inv.id)
    for k, v in fields.items():
        setattr(inv, k, v)
    db.commit()
    vendor_verification_service.run_verification_checks(db, inv.id)
    risk_engine_service.run_risk_assessment(db, inv.id)
    return db.get(Invoice, inv.id)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).filter_by(email="demo@payguard.io").first():
            print("Seed data already present. Skipping.")
            return

        user = User(
            email="demo@payguard.io",
            full_name="Demo Analyst",
            hashed_password=hash_password("demo1234"),
            role="admin",
        )
        db.add(user)

        acme = Vendor(
            legal_name="ACME SUPPLIES LIMITED",
            display_name="ACME Supplies",
            rc_number="RC123456",
            tin="TIN-ACME-001",
            email="billing@acme.example",
            verification_status="unverified",
            onboarding_status="incomplete",
            risk_level="low",
        )
        bright = Vendor(
            legal_name="BRIGHT LOGISTICS NIG LTD",
            display_name="Bright Logistics",
            rc_number="RC777888",
            tin="TIN-BRT-002",
            verification_status="unverified",
            onboarding_status="incomplete",
            risk_level="medium",
        )
        ghost = Vendor(
            legal_name="GHOST TRADING CONCEPTS",
            display_name="Ghost Trading",
            rc_number="RC000000",
            verification_status="unverified",
            onboarding_status="new",
            risk_level="unknown",
        )
        db.add_all([acme, bright, ghost])
        db.commit()
        for v in (acme, bright, ghost):
            db.refresh(v)

        db.add_all(
            [
                VendorBankAccount(
                    vendor_id=acme.id,
                    account_number="0123456789",
                    account_name="ACME SUPPLIES LIMITED",
                    bank_code="058",
                    bank_name="GTBank",
                    is_primary=True,
                ),
                VendorBankAccount(
                    vendor_id=bright.id,
                    account_number="9988776655",
                    account_name="BRIGHT LOGISTICS NIG LTD",
                    bank_code="044",
                    bank_name="Access Bank",
                    is_primary=True,
                ),
            ]
        )
        db.commit()

        # 1. Clean invoice.
        _make_invoice(
            db, user, acme.id, "clean_invoice.txt",
            _invoice_text(vendor="ACME SUPPLIES LIMITED", number="ACME-1001",
                          date="2026-05-01", due="2026-05-30",
                          acct_name="ACME SUPPLIES LIMITED", acct_no="0123456789",
                          bank_code="058", subtotal="500000", tax="37500",
                          total="537500"),
            invoice_number="ACME-1001",
            beneficiary_account_number="0123456789",
            beneficiary_account_name="ACME SUPPLIES LIMITED",
            beneficiary_bank_code="058",
            subtotal=Decimal("500000"), tax_amount=Decimal("37500"),
            total_amount=Decimal("537500"),
        )

        # Build vendor history for ACME so anomaly detection has a baseline.
        _make_invoice(
            db, user, acme.id, "acme_hist.txt",
            _invoice_text(vendor="ACME SUPPLIES LIMITED", number="ACME-1002",
                          date="2026-04-01", due="2026-04-30",
                          acct_name="ACME SUPPLIES LIMITED", acct_no="0123456789",
                          bank_code="058", subtotal="480000", tax="36000",
                          total="516000"),
            invoice_number="ACME-1002",
            beneficiary_account_number="0123456789",
            beneficiary_account_name="ACME SUPPLIES LIMITED",
            beneficiary_bank_code="058",
            total_amount=Decimal("516000"),
        )

        # 2. Duplicate invoice number (same vendor + same number as ACME-1001).
        _make_invoice(
            db, user, acme.id, "duplicate_invoice.txt",
            _invoice_text(vendor="ACME SUPPLIES LIMITED", number="ACME-1001",
                          date="2026-05-02", due="2026-05-31",
                          acct_name="ACME SUPPLIES LIMITED", acct_no="0123456789",
                          bank_code="058", subtotal="500000", tax="37500",
                          total="537500"),
            invoice_number="ACME-1001",
            beneficiary_account_number="0123456789",
            beneficiary_account_name="ACME SUPPLIES LIMITED",
            beneficiary_bank_code="058",
            total_amount=Decimal("537500"),
        )

        # 3. Fake / new unverified vendor.
        _make_invoice(
            db, user, ghost.id, "ghost_vendor.txt",
            _invoice_text(vendor="GHOST TRADING CONCEPTS", number="GH-9001",
                          date="2026-05-10", due="2026-05-20",
                          acct_name="GHOST TRADING CONCEPTS", acct_no="0000000000",
                          bank_code="999", subtotal="900000", tax="67500",
                          total="967500"),
            invoice_number="GH-9001",
            beneficiary_account_number="0000000000",
            beneficiary_account_name="GHOST TRADING CONCEPTS",
            beneficiary_bank_code="999",
            total_amount=Decimal("967500"),
        )

        # 4. Bank account name mismatch (Bright's RC, but wrong account name).
        _make_invoice(
            db, user, bright.id, "account_mismatch.txt",
            _invoice_text(vendor="BRIGHT LOGISTICS NIG LTD", number="BRT-2001",
                          date="2026-05-08", due="2026-06-08",
                          acct_name="UNRELATED PAYEE VENTURES", acct_no="9988776655",
                          bank_code="044", subtotal="300000", tax="22500",
                          total="322500"),
            invoice_number="BRT-2001",
            beneficiary_account_number="9988776655",
            beneficiary_account_name="UNRELATED PAYEE VENTURES",
            beneficiary_bank_code="044",
            total_amount=Decimal("322500"),
        )

        # 5. Inflated amount vs ACME history (~3x average).
        _make_invoice(
            db, user, acme.id, "inflated_invoice.txt",
            _invoice_text(vendor="ACME SUPPLIES LIMITED", number="ACME-1003",
                          date="2026-05-12", due="2026-06-12",
                          acct_name="ACME SUPPLIES LIMITED", acct_no="0123456789",
                          bank_code="058", subtotal="1500000", tax="112500",
                          total="1612500"),
            invoice_number="ACME-1003",
            beneficiary_account_number="0123456789",
            beneficiary_account_name="ACME SUPPLIES LIMITED",
            beneficiary_bank_code="058",
            total_amount=Decimal("1612500"),
        )

        print("Seed complete. Login: demo@payguard.io / demo1234")
    finally:
        db.close()


if __name__ == "__main__":
    main()
