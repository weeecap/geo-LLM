from langchain.tools import tool
from langchain_qdrant import QdrantVectorStore

from utils import get_client, get_embedder

# @tool
# def retrieve(colllection_name:str):
#     client = get_client()
#     embedding = get_embedder()

#     vector_store = QdrantVectorStore(
#         client=client,
#         collection_name=colllection_name,
#         embedding=embedding
# )