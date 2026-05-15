from decimal import Decimal
from types import SimpleNamespace

from app.services.risk_engine_service import RiskContext, evaluate_signals


def _invoice(**kw):
    base = dict(
        invoice_number="INV-1",
        total_amount=Decimal("1000"),
        beneficiary_account_number="0123456789",
        extracted_data={},
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _ctx(**kw):
    defaults = dict(
        invoice=_invoice(),
        duplicate_count=0,
        file_hash_matches=0,
        vendor_history_totals=[],
        account_name_match=True,
        business_verified=True,
        vendor_onboarding_status="complete",
        ocr_confidence=0.95,
        manual_override=False,
    )
    defaults.update(kw)
    return RiskContext(**defaults)


def test_clean_invoice_is_cleared():
    score, verdict, signals, _ = evaluate_signals(_ctx())
    assert score == 0
    assert verdict == "CLEAR"
    assert signals == []


def test_duplicate_invoice_number_scores_30():
    score, verdict, signals, _ = evaluate_signals(_ctx(duplicate_count=1))
    assert score == 30
    assert verdict == "REVIEW"
    assert any(s["signal_code"] == "duplicate_invoice_number" for s in signals)


def test_repeated_file_hash_scores_35():
    score, _, signals, _ = evaluate_signals(_ctx(file_hash_matches=2))
    assert score == 35
    assert any(s["signal_code"] == "repeated_file_hash" for s in signals)


def test_bank_account_mismatch():
    score, _, signals, _ = evaluate_signals(_ctx(account_name_match=False))
    assert score == 25
    assert any(s["signal_code"] == "bank_account_mismatch" for s in signals)


def test_amount_anomaly_over_2x_average():
    ctx = _ctx(
        invoice=_invoice(total_amount=Decimal("5000")),
        vendor_history_totals=[Decimal("1000"), Decimal("1200")],
    )
    score, _, signals, features = evaluate_signals(ctx)
    assert any(s["signal_code"] == "amount_anomaly" for s in signals)
    assert features["invoice_total"] == 5000.0


def test_missing_mandatory_fields():
    ctx = _ctx(invoice=_invoice(invoice_number=None))
    _, _, signals, _ = evaluate_signals(ctx)
    assert any(s["signal_code"] == "missing_mandatory_fields" for s in signals)


def test_block_when_score_exceeds_75():
    ctx = _ctx(
        duplicate_count=1,        # 30
        file_hash_matches=1,      # 35
        account_name_match=False, # 25
    )
    score, verdict, _, _ = evaluate_signals(ctx)
    assert score >= 75
    assert verdict == "BLOCK"


def test_score_capped_at_100():
    ctx = _ctx(
        duplicate_count=1,
        file_hash_matches=1,
        account_name_match=False,
        business_verified=False,
        vendor_onboarding_status="new",
        ocr_confidence=0.2,
        manual_override=True,
        invoice=_invoice(invoice_number=None),
    )
    score, verdict, _, _ = evaluate_signals(ctx)
    assert score == 100
    assert verdict == "BLOCK"
