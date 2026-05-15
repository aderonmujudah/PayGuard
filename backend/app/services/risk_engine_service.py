"""Rule-based weighted risk engine.

Pure scoring logic lives in `evaluate_signals` (unit-tested without a DB).
`run_risk_assessment` gathers DB context, calls the pure function, and
persists the assessment + individual signals.
"""

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Invoice, RiskAssessment, RiskSignal, VerificationCheck
from app.repositories import invoice_repository
from app.services import audit_service

# code -> (label, score, severity)
SIGNAL_CATALOG: dict[str, tuple[str, int, str]] = {
    "duplicate_invoice_number": ("Duplicate invoice number from same vendor", 30, "high"),
    "repeated_file_hash": ("Identical file uploaded before", 35, "high"),
    "bank_account_mismatch": ("Beneficiary account name mismatch", 25, "high"),
    "amount_anomaly": ("Amount far above vendor average", 20, "medium"),
    "new_vendor_incomplete": ("New vendor with incomplete verification", 15, "medium"),
    "low_ocr_confidence": ("Low OCR confidence", 5, "low"),
    "missing_mandatory_fields": ("Missing mandatory invoice fields", 10, "medium"),
    "manual_override_flag": ("Suspicious manual override flag", 20, "high"),
}

MANDATORY_FIELDS = ("invoice_number", "total_amount", "beneficiary_account_number")


@dataclass
class RiskContext:
    invoice: Invoice
    duplicate_count: int
    file_hash_matches: int
    vendor_history_totals: list[Decimal]
    account_name_match: bool | None
    business_verified: bool | None
    vendor_onboarding_status: str | None
    ocr_confidence: float
    manual_override: bool


def evaluate_signals(ctx: RiskContext) -> tuple[int, str, list[dict], dict]:
    """Return (score, verdict, signals, features). No DB access here."""
    signals: list[dict] = []
    features: dict = {}

    def add(code: str, details: dict) -> None:
        label, score, severity = SIGNAL_CATALOG[code]
        signals.append(
            {
                "signal_code": code,
                "signal_label": label,
                "severity": severity,
                "signal_score": score,
                "details": details,
            }
        )

    inv = ctx.invoice

    if ctx.duplicate_count > 0:
        add("duplicate_invoice_number", {"matches": ctx.duplicate_count})
    features["duplicate_count"] = ctx.duplicate_count

    if ctx.file_hash_matches > 0:
        add("repeated_file_hash", {"matches": ctx.file_hash_matches})
    features["file_hash_matches"] = ctx.file_hash_matches

    if ctx.account_name_match is False:
        add("bank_account_mismatch", {"account_name_match": False})
    features["account_name_match"] = ctx.account_name_match

    avg = (
        float(sum(ctx.vendor_history_totals) / len(ctx.vendor_history_totals))
        if ctx.vendor_history_totals
        else 0.0
    )
    total = float(inv.total_amount or 0)
    features["vendor_average_amount"] = round(avg, 2)
    features["invoice_total"] = total
    if avg > 0 and total > 2 * avg:
        add(
            "amount_anomaly",
            {"invoice_total": total, "vendor_average": round(avg, 2), "threshold": "2x"},
        )

    if (ctx.business_verified is not True) and ctx.vendor_onboarding_status in (
        None,
        "new",
        "incomplete",
    ):
        add(
            "new_vendor_incomplete",
            {
                "business_verified": ctx.business_verified,
                "onboarding_status": ctx.vendor_onboarding_status,
            },
        )

    if ctx.ocr_confidence and ctx.ocr_confidence < 0.6:
        add("low_ocr_confidence", {"ocr_confidence": ctx.ocr_confidence})
    features["ocr_confidence"] = ctx.ocr_confidence

    missing = [
        f for f in MANDATORY_FIELDS if not getattr(inv, f, None)
    ]
    if missing:
        add("missing_mandatory_fields", {"missing": missing})
    features["missing_fields"] = missing

    if ctx.manual_override:
        add("manual_override_flag", {"flagged": True})

    score = min(100, sum(s["signal_score"] for s in signals))

    if score <= 24:
        verdict = "CLEAR"
    elif score <= 49:
        verdict = "REVIEW"
    elif score <= 74:
        verdict = "HOLD"
    else:
        verdict = "BLOCK"

    return score, verdict, signals, features


def build_explanation(score: int, verdict: str, signals: list[dict]) -> str:
    if not signals:
        return (
            f"Score {score}/100 -> {verdict}. No risk signals triggered; "
            f"all mandatory fields present and checks passed."
        )
    lines = [f"Score {score}/100 -> {verdict}. Triggered signals:"]
    for s in sorted(signals, key=lambda x: -x["signal_score"]):
        lines.append(
            f"  - [{s['severity'].upper()}] {s['signal_label']} (+{s['signal_score']})"
        )
    return "\n".join(lines)


def run_risk_assessment(db: Session, invoice_id: uuid.UUID) -> RiskAssessment:
    invoice = invoice_repository.get(db, invoice_id)
    if invoice is None:
        raise ValueError("Invoice not found")

    dup = invoice_repository.find_duplicates_by_number(
        db, invoice.vendor_id, invoice.invoice_number, invoice.id
    )
    hash_matches = invoice_repository.find_by_file_hash(
        db, invoice.file_hash, invoice.id
    )
    history = invoice_repository.vendor_invoice_history(
        db, invoice.vendor_id, invoice.id
    )

    acct_check = db.execute(
        select(VerificationCheck)
        .where(
            VerificationCheck.invoice_id == invoice.id,
            VerificationCheck.check_type == "account_verification",
        )
        .order_by(VerificationCheck.created_at.desc())
    ).scalars().first()
    biz_check = db.execute(
        select(VerificationCheck)
        .where(
            VerificationCheck.invoice_id == invoice.id,
            VerificationCheck.check_type == "business_verification",
        )
        .order_by(VerificationCheck.created_at.desc())
    ).scalars().first()

    account_name_match = (
        acct_check.normalized_result.get("name_match") if acct_check else None
    )
    business_verified = (
        biz_check.normalized_result.get("verified") if biz_check else None
    )

    ctx = RiskContext(
        invoice=invoice,
        duplicate_count=len(dup),
        file_hash_matches=len(hash_matches),
        vendor_history_totals=[i.total_amount for i in history if i.total_amount],
        account_name_match=account_name_match,
        business_verified=business_verified,
        vendor_onboarding_status=(
            invoice.vendor.onboarding_status if invoice.vendor else None
        ),
        ocr_confidence=invoice.ocr_confidence or 0.0,
        manual_override=bool(invoice.extracted_data.get("manual_override")),
    )

    score, verdict, signals, features = evaluate_signals(ctx)
    explanation = build_explanation(score, verdict, signals)

    assessment = RiskAssessment(
        invoice_id=invoice.id,
        score=score,
        verdict=verdict,
        explanation=explanation,
        features=features,
    )
    db.add(assessment)
    db.flush()
    for s in signals:
        db.add(RiskSignal(assessment_id=assessment.id, **s))

    status_map = {
        "CLEAR": "cleared",
        "REVIEW": "review",
        "HOLD": "hold",
        "BLOCK": "blocked",
    }
    invoice.status = status_map[verdict]

    audit_service.record(
        db,
        entity_type="invoice",
        entity_id=invoice.id,
        action="risk_assessed",
        new_values={"score": score, "verdict": verdict},
        metadata={"signals": [s["signal_code"] for s in signals]},
    )
    db.commit()
    db.refresh(assessment)
    return assessment
