from torch import Tensor
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

from llm.settings import settings
from llm.utils import logger

class QueryEmbeddings(Embeddings):
    """
    A LangChain-compatible embedding wrapper for SentenceTransformer models
    Class wraps a SentenceTransformer model and implements LangChain interface
    
    Args:
        model_name (str, optional): The name or path of the SentenceTransformer model
            to load
    """
    def __init__(self, model_name:str=settings.embedding.model_name) -> None:
        super().__init__()
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        logger.info('embed_document function is called')
        passages = [f"passage: {text}" for text in texts]
        embeddings = self.model.encode(
            passages,
            normalize_embeddings=True,
            convert_to_numpy=False
        )
    
        if isinstance(embeddings, Tensor):
            embeddings = embeddings.cpu().tolist()
        return embeddings
    
    def embed_query(self, text: str) -> list[float]:
        logger.info('embed_query function is called')
        query = f'query: {text}'
        embeddings =  self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=False  
        )
        
        if isinstance(embeddings, Tensor):
            embeddings = embeddings.cpu().tolist()
        return embeddings
    
class EmbeddingManager:
    """
    Singleton manager for LangChain-compatible embedding instances.
    
    Provides thread-safe lazy initialization and centralized access to a single
    SentenceTransformer embedding instance throughout the application lifecycle.
    Ensures efficient resource usage by preventing redundant model loading into
    memory while maintaining LangChain Embeddings interface compatibility.
    """
    
    _instance:QueryEmbeddings | None=None

    @classmethod
    def get_instance(cls) -> QueryEmbeddings:
        if cls._instance is None:
            cls._instance = QueryEmbeddings(settings.embedding.model_name)
        return cls._instance