from app.services.invoice_extraction_engine import (
    HeuristicInvoiceExtractionEngine,
    HybridInvoiceExtractionEngine,
    LocalModelInvoiceExtractionEngine,
)

SAMPLE = """INVOICE
Vendor: ACME SUPPLIES LIMITED
Invoice Number: ACME-1001
Invoice Date: 2026-05-01
Due Date: 2026-05-30
Account Name: ACME SUPPLIES LIMITED
Account Number: 0123456789
Bank Code: 058
Subtotal: 500000
VAT (7.5%): 37500
Grand Total: 537500
"""


def test_heuristic_extracts_core_fields():
    engine = HeuristicInvoiceExtractionEngine()
    out = engine.extract(text=SAMPLE, ocr_confidence=0.95)
    assert out["invoice_number"] == "ACME-1001"
    assert out["invoice_date"] == "2026-05-01"
    assert out["total_amount"] == 537500.0
    assert out["beneficiary_account_number"] == "0123456789"
    assert out["engine"] == "heuristic"


def test_heuristic_handles_empty_text():
    engine = HeuristicInvoiceExtractionEngine()
    out = engine.extract(text="", ocr_confidence=0.0)
    assert out["invoice_number"] is None
    assert out["total_amount"] == 0.0


def test_local_model_unavailable_raises():
    engine = LocalModelInvoiceExtractionEngine()
    assert engine.available is False
    try:
        engine.extract(text=SAMPLE, ocr_confidence=0.9)
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


def test_hybrid_falls_back_to_heuristic_when_no_model():
    engine = HybridInvoiceExtractionEngine()
    out = engine.extract(text=SAMPLE, ocr_confidence=0.95)
    assert out["invoice_number"] == "ACME-1001"
    assert out["engine"] == "hybrid:heuristic_fallback"


def test_stable_schema_keys_present():
    engine = HeuristicInvoiceExtractionEngine()
    out = engine.extract(text=SAMPLE, ocr_confidence=0.9)
    for key in (
        "invoice_number",
        "currency_code",
        "total_amount",
        "line_items",
        "field_confidence",
        "engine",
    ):
        assert key in out
