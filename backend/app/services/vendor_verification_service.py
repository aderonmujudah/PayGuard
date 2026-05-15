import uuid

from sqlalchemy.orm import Session

from app.models import Invoice, VendorBankAccount, VerificationCheck
from app.providers.registry import (
    get_account_verification_provider,
    get_business_verification_provider,
)
from app.repositories import vendor_repository
from app.services import audit_service


def run_verification_checks(
    db: Session, invoice_id: uuid.UUID
) -> list[VerificationCheck]:
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise ValueError("Invoice not found")

    invoice.status = "verifying"
    db.flush()

    checks: list[VerificationCheck] = []
    vendor = (
        vendor_repository.get(db, invoice.vendor_id) if invoice.vendor_id else None
    )

    # 1. Account (beneficiary) verification.
    acct_provider = get_account_verification_provider()
    acct_no = invoice.beneficiary_account_number or ""
    bank_code = invoice.beneficiary_bank_code or ""
    acct_req = {"account_number": acct_no, "bank_code": bank_code}
    acct_res = acct_provider.verify_account(acct_no, bank_code)

    name_match = False
    if acct_res.get("resolved") and invoice.beneficiary_account_name:
        name_match = (
            acct_res["account_name"].strip().lower()
            == invoice.beneficiary_account_name.strip().lower()
        )
    normalized_acct = {
        "resolved": acct_res.get("resolved", False),
        "resolved_name": acct_res.get("account_name"),
        "claimed_name": invoice.beneficiary_account_name,
        "name_match": name_match,
    }
    acct_check = VerificationCheck(
        invoice_id=invoice.id,
        vendor_id=invoice.vendor_id,
        check_type="account_verification",
        provider_name=acct_provider.name,
        status="passed" if (acct_res.get("resolved") and name_match) else "failed",
        request_payload=acct_req,
        response_payload=acct_res,
        normalized_result=normalized_acct,
    )
    db.add(acct_check)
    checks.append(acct_check)

    # 2. Business verification.
    biz_provider = get_business_verification_provider()
    if vendor:
        biz_req = {
            "rc_number": vendor.rc_number,
            "tin": vendor.tin,
            "legal_name": vendor.legal_name,
        }
        biz_res = biz_provider.verify_business(
            vendor.rc_number, vendor.tin, vendor.legal_name
        )
        biz_check = VerificationCheck(
            invoice_id=invoice.id,
            vendor_id=vendor.id,
            check_type="business_verification",
            provider_name=biz_provider.name,
            status="passed" if biz_res.get("verified") else "failed",
            request_payload=biz_req,
            response_payload=biz_res,
            normalized_result={
                "verified": biz_res.get("verified", False),
                "registered_name": biz_res.get("registered_name"),
                "status": biz_res.get("status"),
            },
        )
        db.add(biz_check)
        checks.append(biz_check)

        # Update vendor verification status.
        vendor.verification_status = (
            "verified" if biz_res.get("verified") else "failed"
        )
        if biz_res.get("verified") and name_match:
            vendor.onboarding_status = "complete"

        # Mark matching bank account verified.
        for ba in vendor.bank_accounts:
            if ba.account_number == acct_no and acct_res.get("resolved"):
                ba.is_verified = name_match

    invoice.status = "verified"
    audit_service.record(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="verification_completed",
        new_values={"checks": [c.check_type + ":" + c.status for c in checks]},
    )
    db.commit()
    for c in checks:
        db.refresh(c)
    return checks
