from qdrant_client import QdrantClient

from llm.utils import logger
from llm.settings import settings

class QdrantManager:
    """
    Singleton manager for Qdrant vector database client instances.
    
    Provides centralized, lazy-initialized access to a single QdrantClient instance
    configured from application settings. Ensures efficient connection reuse and
    prevents redundant client initialization across the application lifecycle.
    """
    _client:QdrantClient | None=None
    
    @classmethod
    def get_instance(cls):
        if cls._client is None:
            cls._client = QdrantClient(
            host=settings.qdrant.host,
            port=settings.qdrant.port
            )
        
        logger.info("Qdrant client was loaded")
        return cls._client