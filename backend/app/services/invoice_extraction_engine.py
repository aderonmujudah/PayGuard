"""Pluggable invoice extraction.

Stable output schema (the contract every engine must satisfy):

{
  "invoice_number": str | None,
  "invoice_date": "YYYY-MM-DD" | None,
  "due_date": "YYYY-MM-DD" | None,
  "currency_code": str,
  "subtotal": float,
  "tax_amount": float,
  "total_amount": float,
  "vendor_name": str | None,
  "beneficiary_account_number": str | None,
  "beneficiary_account_name": str | None,
  "beneficiary_bank_code": str | None,
  "line_items": [{"description": str, "quantity": float,
                  "unit_price": float, "line_total": float}],
  "field_confidence": {field: float},
  "engine": str
}

Engines:
- HeuristicInvoiceExtractionEngine  -> regex/keyword parsing of OCR text.
- LocalModelInvoiceExtractionEngine -> loads artifacts from LOCAL_MODEL_DIR
  once at startup; you drop your Colab-trained model in later.
- HybridInvoiceExtractionEngine     -> model first, heuristic fills gaps,
  heuristic-only fallback if the model is unavailable.
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from app.core.config import settings

STABLE_FIELDS = [
    "invoice_number",
    "invoice_date",
    "due_date",
    "currency_code",
    "subtotal",
    "tax_amount",
    "total_amount",
    "vendor_name",
    "beneficiary_account_number",
    "beneficiary_account_name",
    "beneficiary_bank_code",
]


def _empty_result(engine: str) -> dict[str, Any]:
    return {
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None,
        "currency_code": "NGN",
        "subtotal": 0.0,
        "tax_amount": 0.0,
        "total_amount": 0.0,
        "vendor_name": None,
        "beneficiary_account_number": None,
        "beneficiary_account_name": None,
        "beneficiary_bank_code": None,
        "line_items": [],
        "field_confidence": {},
        "engine": engine,
    }


class InvoiceExtractionEngine(ABC):
    name: str = "base"

    @abstractmethod
    def extract(self, *, text: str, ocr_confidence: float) -> dict[str, Any]:
        """Return a dict matching the stable schema above."""


# --------------------------------------------------------------------------- #
# Heuristic engine
# --------------------------------------------------------------------------- #
_NUM = r"[\d,]+(?:\.\d{1,2})?"


def _to_float(raw: str | None) -> float:
    if not raw:
        return 0.0
    try:
        return float(raw.replace(",", "").strip())
    except ValueError:
        return 0.0


def _parse_date(raw: str | None) -> str | None:
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


class HeuristicInvoiceExtractionEngine(InvoiceExtractionEngine):
    name = "heuristic"

    def extract(self, *, text: str, ocr_confidence: float) -> dict[str, Any]:
        result = _empty_result(self.name)
        if not text:
            return result
        t = text
        conf: dict[str, float] = {}

        def search(pattern: str, group: int = 1) -> str | None:
            m = re.search(pattern, t, re.IGNORECASE)
            return m.group(group).strip() if m else None

        inv_no = search(r"invoice\s*(?:no\.?|number|#)\s*[:\-]?\s*([A-Z0-9\-\/]+)")
        if inv_no:
            result["invoice_number"] = inv_no
            conf["invoice_number"] = 0.85

        inv_date = _parse_date(
            search(r"invoice\s*date\s*[:\-]?\s*([0-9A-Za-z\/\-\s]{6,20})")
        )
        if inv_date:
            result["invoice_date"] = inv_date
            conf["invoice_date"] = 0.8

        due = _parse_date(search(r"due\s*date\s*[:\-]?\s*([0-9A-Za-z\/\-\s]{6,20})"))
        if due:
            result["due_date"] = due
            conf["due_date"] = 0.75

        cur = search(r"\b(NGN|USD|EUR|GBP|NGN|₦|\$)\b")
        if cur:
            result["currency_code"] = {"₦": "NGN", "$": "USD"}.get(cur, cur)
            conf["currency_code"] = 0.6

        total = _to_float(search(rf"(?:grand\s*)?total\s*(?:due)?\s*[:\-]?\s*[₦$]?\s*({_NUM})"))
        if total:
            result["total_amount"] = total
            conf["total_amount"] = 0.8
        subtotal = _to_float(search(rf"sub\s*total\s*[:\-]?\s*[₦$]?\s*({_NUM})"))
        if subtotal:
            result["subtotal"] = subtotal
            conf["subtotal"] = 0.75
        tax = _to_float(search(rf"(?:tax|vat)\s*(?:\(\d+%\))?\s*[:\-]?\s*[₦$]?\s*({_NUM})"))
        if tax:
            result["tax_amount"] = tax
            conf["tax_amount"] = 0.7

        if not result["subtotal"] and result["total_amount"]:
            result["subtotal"] = round(result["total_amount"] - result["tax_amount"], 2)

        acct = search(r"account\s*(?:no\.?|number)\s*[:\-]?\s*(\d{10})")
        if acct:
            result["beneficiary_account_number"] = acct
            conf["beneficiary_account_number"] = 0.8
        acct_name = search(r"account\s*name\s*[:\-]?\s*([A-Za-z0-9 &.\-]{3,60})")
        if acct_name:
            result["beneficiary_account_name"] = acct_name.strip()
            conf["beneficiary_account_name"] = 0.7
        bank_code = search(r"bank\s*code\s*[:\-]?\s*(\d{3})")
        if bank_code:
            result["beneficiary_bank_code"] = bank_code
            conf["beneficiary_bank_code"] = 0.7

        vendor = search(r"(?:from|vendor|supplier|bill\s*from)\s*[:\-]?\s*([A-Za-z0-9 &.\-]{3,60})")
        if vendor:
            result["vendor_name"] = vendor.strip()
            conf["vendor_name"] = 0.55

        result["field_confidence"] = conf
        return result


# --------------------------------------------------------------------------- #
# Local model engine
# --------------------------------------------------------------------------- #
class LocalModelInvoiceExtractionEngine(InvoiceExtractionEngine):
    """Loads model artifacts once. Drop your trained model into
    settings.LOCAL_MODEL_DIR and implement `_predict`.

    Expected directory contents (example):
      /models/invoice_extractor/
        model.safetensors | pytorch_model.bin
        config.json
        tokenizer.json
        adapter/  (optional LoRA)
    """

    name = "local_model"

    def __init__(self) -> None:
        self.available = False
        self.model = None
        self._load()

    def _load(self) -> None:
        model_dir = settings.LOCAL_MODEL_DIR
        if not os.path.isdir(model_dir):
            return
        has_artifacts = any(
            os.path.exists(os.path.join(model_dir, f))
            for f in ("model.safetensors", "pytorch_model.bin", "config.json")
        )
        if not has_artifacts:
            return
        try:
            # Replace this block with real loading, e.g.:
            #   from transformers import AutoModelForTokenClassification, AutoTokenizer
            #   self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
            #   self.model = AutoModelForTokenClassification.from_pretrained(model_dir)
            self.model = {"loaded_from": model_dir}
            self.available = True
        except Exception:
            self.available = False

    def _predict(self, text: str) -> dict[str, Any]:
        """Run inference and map raw model output to the stable schema.

        Implement once your Colab model is in place. Until then this raises
        so HybridInvoiceExtractionEngine cleanly falls back to heuristics.
        """
        raise NotImplementedError(
            "LocalModelInvoiceExtractionEngine._predict not implemented yet. "
            "Add inference once the trained model is in LOCAL_MODEL_DIR."
        )

    def extract(self, *, text: str, ocr_confidence: float) -> dict[str, Any]:
        if not self.available:
            raise RuntimeError("Local model not available")
        raw = self._predict(text)
        result = _empty_result(self.name)
        for f in STABLE_FIELDS + ["line_items", "field_confidence"]:
            if f in raw:
                result[f] = raw[f]
        result["engine"] = self.name
        return result


# --------------------------------------------------------------------------- #
# Hybrid engine
# --------------------------------------------------------------------------- #
class HybridInvoiceExtractionEngine(InvoiceExtractionEngine):
    name = "hybrid"

    def __init__(
        self,
        model_engine: LocalModelInvoiceExtractionEngine | None = None,
        heuristic_engine: HeuristicInvoiceExtractionEngine | None = None,
    ) -> None:
        self.model_engine = model_engine or LocalModelInvoiceExtractionEngine()
        self.heuristic_engine = heuristic_engine or HeuristicInvoiceExtractionEngine()

    def extract(self, *, text: str, ocr_confidence: float) -> dict[str, Any]:
        heuristic = self.heuristic_engine.extract(text=text, ocr_confidence=ocr_confidence)
        try:
            model_out = self.model_engine.extract(text=text, ocr_confidence=ocr_confidence)
        except (RuntimeError, NotImplementedError):
            heuristic["engine"] = "hybrid:heuristic_fallback"
            return heuristic

        merged = dict(heuristic)
        for field in STABLE_FIELDS:
            mv = model_out.get(field)
            if mv not in (None, "", 0, 0.0):
                merged[field] = mv
        if model_out.get("line_items"):
            merged["line_items"] = model_out["line_items"]
        merged["field_confidence"] = {
            **heuristic.get("field_confidence", {}),
            **model_out.get("field_confidence", {}),
        }
        merged["engine"] = "hybrid:model+heuristic"
        return merged


# --------------------------------------------------------------------------- #
# Startup singleton — model loads ONCE, not per request.
# --------------------------------------------------------------------------- #
_ENGINE: InvoiceExtractionEngine | None = None


def init_extraction_engine() -> InvoiceExtractionEngine:
    global _ENGINE
    mode = settings.INVOICE_EXTRACTION_MODE
    if mode == "heuristic":
        _ENGINE = HeuristicInvoiceExtractionEngine()
    elif mode == "local_model":
        _ENGINE = LocalModelInvoiceExtractionEngine()
    else:
        _ENGINE = HybridInvoiceExtractionEngine()
    return _ENGINE


def get_extraction_engine() -> InvoiceExtractionEngine:
    if _ENGINE is None:
        return init_extraction_engine()
    return _ENGINE
