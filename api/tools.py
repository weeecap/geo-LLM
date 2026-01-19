from typing import List

from langchain.tools import tool
from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document

from utils import get_client, get_embedder

@tool
def retrieve(query:str) -> str:
    """Search Qdrant documentation for relevant information based on the user's question."""

    client = get_client()
    embedding = get_embedder()

    vector_store = QdrantVectorStore(
        client=client,
        collection_name='document',
        embedding=embedding
)
    
    retriever = vector_store.as_retriever(
        search_type='similarity',
        search_kwargs={'k':5}
    )

    docs = retriever.invoke(query)

    if docs and hasattr(docs[0], 'page_content'):
        return docs[0].page_content
    return "No relevant information found in the documentation."
