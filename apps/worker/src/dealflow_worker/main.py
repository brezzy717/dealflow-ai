import logging
from rq import Queue
from redis import Redis


logger = logging.getLogger(__name__)


def create_queue(redis_url: str = "redis://localhost:6379/0") -> Queue:
    connection = Redis.from_url(redis_url)
    return Queue("dealflow-tasks", connection=connection)


if __name__ == "__main__":
    queue = create_queue()
    logger.info("Worker started", queue_name=queue.name)
