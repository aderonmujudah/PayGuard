from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    audit,
    auth,
    dashboard,
    files,
    invoices,
    payments,
    pipeline,
    vendors,
)
from app.core.config import settings
from app.services.invoice_extraction_engine import init_extraction_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Model loads ONCE at startup, not per request.
    engine = init_extraction_engine()
    app.state.extraction_engine = engine.name
    yield


app = FastAPI(
    title="PayGuard API",
    version="0.1.0",
    description="AI-powered invoice & vendor verification for B2B payments.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, dashboard, invoices, pipeline, vendors, payments, audit, files):
    app.include_router(r.router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "extraction_engine": settings.INVOICE_EXTRACTION_MODE}
