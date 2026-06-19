import os

import structlog
from redis import Redis
from rq import Queue

logger = structlog.get_logger(__name__)


def create_queue(redis_url: str | None = None) -> Queue:
    url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    connection = Redis.from_url(url)
    return Queue("dealflow-tasks", connection=connection)


def main() -> None:
    queue = create_queue()
    logger.info("worker_started", queue_name=queue.name)


if __name__ == "__main__":
    main()
