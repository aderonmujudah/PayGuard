"""Entrypoint: `python -m app.workers.worker` to consume the RQ queue."""

from redis import Redis
from rq import Queue, Worker

from app.core.config import settings


def main() -> None:
    conn = Redis.from_url(settings.REDIS_URL)
    worker = Worker([Queue("payguard", connection=conn)], connection=conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
