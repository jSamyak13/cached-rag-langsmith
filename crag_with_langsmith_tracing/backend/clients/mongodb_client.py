import logging
from pymongo import MongoClient
from crag_with_langsmith_tracing.backend.config.settings import settings

logger = logging.getLogger(__name__)

try:
    mongo_client = MongoClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=2000
    )
    mongo_client.admin.command("ping")
    logger.info("MongoDB client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize MongoDB client: {e}")
    mongo_client = None
