import redis
import logging
from crag_with_langsmith_tracing.backend.config.settings import settings

logger = logging.getLogger(__name__)

try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True
    )
    redis_client.ping()
except Exception as e:
    logger.error(f"Failed to initialize Redis client: {e}")
    redis_client = None
