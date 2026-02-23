from langchain_qdrant import QdrantVectorStore
from langchain.tools import tool 
from langchain_core.utils.function_calling import convert_to_openai_tool
from typing import List

from utils.embedder import EmbeddingManager
from utils.qdrant_client import QdrantManager
from .utils import logger

@tool(response_format='content_and_artifact')
def retrieve_context(query:str):

    "Retrieve information to help answer a query"
    
    logger.info('Retrieve_contex function has been call')
    client = QdrantManager.get_instance()
    embedding = EmbeddingManager.get_instance()

    vector_store = QdrantVectorStore(
        client=client,
        collection_name='document',
        embedding=embedding
    )
    logger.info(f"Vector store {vector_store} was init")
    retrieved_docs = vector_store.similarity_search(query,k=3)
    serialized = "\n\n".join(
        (f"Source:{doc.metadata}\nContent:{doc.page_content}")
        for doc in retrieved_docs
    )
    logger.info(retrieved_docs, serialized)
    return serialized

def get_openai_tool() -> List[dict]:
    functions = [retrieve_context]
    tools = [convert_to_openai_tool(f) for f in functions]
    return tools

