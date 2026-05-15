# PayGuard

AI-powered invoice & vendor verification platform for B2B payments.

Upload an invoice → extract structured fields (OCR + pluggable model) →
verify vendor & beneficiary account → compute a rule-based fraud risk
score → get an explainable verdict (**CLEAR / REVIEW / HOLD / BLOCK**) →
trigger a (mocked) payment action → everything written to an audit trail.

> The real Squad payment integration is **intentionally not built**.
> Payments go through a clean `PaymentProvider` abstraction with a
> `MockSquadPaymentProvider`. Swap it in `app/providers/registry.py`
> later with zero changes to callers.

## Stack

| Layer    | Tech                                                |
|----------|-----------------------------------------------------|
| Frontend | Next.js (App Router) · TypeScript · Tailwind        |
| Backend  | FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2      |
| Data     | PostgreSQL · Redis (RQ jobs)                        |
| Storage  | Local (dev) · S3-compatible abstraction (prod)      |
| Infra    | Docker Compose                                       |

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
make up          # or: docker compose up --build
```

This starts Postgres, Redis, backend (runs migrations + seeds demo data),
the RQ worker, and the frontend.

- Frontend: http://localhost:3000
- API docs (OpenAPI/Swagger): http://localhost:8000/docs
- Login: **demo@payguard.io / demo1234**

```bash
make seed     # re-run seed (idempotent)
make test     # backend unit tests
make fresh    # wipe volumes and rebuild
```

## Local dev (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# point DATABASE_URL/REDIS_URL in .env at local services
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Demo flow

1. **Login** with the demo credentials.
2. **Dashboard** — counts by status, held/blocked/cleared metrics, recent activity.
3. **Upload** a PDF/image/`.txt` invoice → extraction runs automatically.
4. **Invoice detail** — review/edit extracted fields (with per-field
   confidence), run verification, run risk assessment, see the explainable
   verdict & triggered signals, then Release / Hold / Block payment.
5. **Review queue** — everything flagged REVIEW or HOLD.
6. **Payment log** & **Audit trail** — full history.

Seed data ships 5 scenarios: clean, duplicate invoice number, fake/new
vendor, account-name mismatch, inflated amount.

## Architecture

```
backend/app/
  api/          REST routes + auth deps
  core/         config, db, security
  models/       SQLAlchemy ORM (10 tables)
  schemas/      Pydantic I/O
  repositories/ query helpers
  services/     file_storage, ocr, invoice_extraction_engine,
                invoice_parser, vendor_verification, risk_engine,
                payment, audit
  providers/    AccountVerification / BusinessVerification /
                PaymentProvider interfaces + Mock implementations
  workers/      RQ background jobs (sync fallback for MVP)
frontend/app/   Next.js App Router pages
models/invoice_extractor/   drop trained model artifacts here
```

### Pluggable extraction engine

`InvoiceExtractionEngine` interface with three implementations:

- `HeuristicInvoiceExtractionEngine` — regex/keyword parsing of OCR text.
- `LocalModelInvoiceExtractionEngine` — loads artifacts from
  `LOCAL_MODEL_DIR` **once at startup**; implement `_predict` for your
  Colab-trained model.
- `HybridInvoiceExtractionEngine` — model first, heuristic fills gaps,
  **automatic heuristic fallback** when the model is unavailable.

Switch via `INVOICE_EXTRACTION_MODE` (`heuristic|local_model|hybrid`).
See `models/invoice_extractor/README.md` for the integration steps.

### Risk engine

Rule-based weighted signals (`app/services/risk_engine_service.py`). Pure
scoring lives in `evaluate_signals()` and is unit-tested without a DB.

| Signal | Score |
|---|---|
| Repeated file hash | +35 |
| Duplicate invoice number | +30 |
| Bank account name mismatch | +25 |
| Amount > 2× vendor average | +20 |
| Suspicious manual override | +20 |
| New vendor incomplete verification | +15 |
| Missing mandatory fields | +10 |
| Low OCR confidence | +5 |

Verdicts: `0–24 CLEAR · 25–49 REVIEW · 50–74 HOLD · 75–100 BLOCK`.
Both the overall assessment and individual signals are persisted.

## Integration hooks (for later)

- **Real Squad**: implement `PaymentProvider` and return it from
  `app/providers/registry.py:get_payment_provider()`.
- **Trained model**: place artifacts in `models/invoice_extractor/`,
  implement `LocalModelInvoiceExtractionEngine._predict`.
- **S3 storage**: set `STORAGE_BACKEND=s3` + S3 vars in `.env`.
- **Background jobs**: set `USE_BACKGROUND_JOBS=true` (RQ worker already
  wired in compose).

## API

Full interactive docs at `/docs`. A Postman collection is included:
`PayGuard.postman_collection.json`.
