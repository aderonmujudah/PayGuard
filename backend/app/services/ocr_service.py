"""OCR with graceful fallback.

- PDFs: try text layer via pdfplumber first.
- Images / scanned PDFs: try pytesseract if available.
- If nothing works, return empty text with confidence 0 so the pipeline
  can still proceed on heuristics.
"""

import io

from app.core.config import settings


def _ocr_image(data: bytes) -> tuple[str, float]:
    try:
        import pytesseract
        from PIL import Image

        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
        img = Image.open(io.BytesIO(data))
        ocr = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        words = [w for w in ocr["text"] if w.strip()]
        confs = [int(c) for c in ocr["conf"] if str(c).lstrip("-").isdigit() and int(c) >= 0]
        text = " ".join(words)
        confidence = (sum(confs) / len(confs) / 100.0) if confs else 0.0
        return text, round(confidence, 4)
    except Exception:
        return "", 0.0


def _extract_pdf(data: bytes) -> tuple[str, float]:
    try:
        import pdfplumber

        text_parts: list[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
        text = "\n".join(text_parts).strip()
        if text:
            # Native text layer => high confidence.
            return text, 0.97
    except Exception:
        pass
    # Scanned PDF with no text layer -> fall back to image OCR of raw bytes.
    return _ocr_image(data)


def run_ocr(filename: str, data: bytes) -> dict:
    if not settings.OCR_ENABLED:
        return {"status": "skipped", "text": "", "confidence": 0.0}

    lower = filename.lower()
    if lower.endswith(".pdf"):
        text, confidence = _extract_pdf(data)
    elif lower.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")):
        text, confidence = _ocr_image(data)
    else:
        text, confidence = "", 0.0

    status = "done" if text else "failed"
    return {"status": status, "text": text, "confidence": confidence}
