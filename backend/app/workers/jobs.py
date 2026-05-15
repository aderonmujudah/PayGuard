"""Background job hooks.

MVP keeps complexity low: if USE_BACKGROUND_JOBS is off (default), the
extraction pipeline runs synchronously in-process. If on, it is enqueued
to Redis via RQ and processed by `rq worker payguard`.
"""

import uuid

from app.core.config import settings


def _run_extraction(invoice_id_str: str) -> None:
    from app.core.database import SessionLocal
    from app.services.invoice_parser_service import run_extraction_pipeline

    db = SessionLocal()
    try:
        run_extraction_pipeline(db, uuid.UUID(invoice_id_str))
    finally:
        db.close()


def get_queue():
    from redis import Redis
    from rq import Queue

    return Queue("payguard", connection=Redis.from_url(settings.REDIS_URL))


def enqueue_extraction(invoice_id: uuid.UUID) -> None:
    if settings.USE_BACKGROUND_JOBS:
        get_queue().enqueue(_run_extraction, str(invoice_id))
    else:
        _run_extraction(str(invoice_id))
