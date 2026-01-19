from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import logging

from schemas import PlotProperties
from settings import settings

VECTOR_SIZE = settings.embedding.vector_size

_embedder = None
_client = None

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='logs.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
        passages = [f"passage: {text}" for text in texts]
        return self.model.encode(
            passages,
            normalize_embeddings=True,
            convert_to_numpy=False
        ).tolist()
    
    def embed_query(self, text: str) -> list[float]:
        query = f'query: {text}'
        return self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=False  
        ).tolist()

def get_embedder():
    """
     Defining embedder using singleton pattern
    """
    global _embedder
    if _embedder is None:
        embedding_model = settings.embedding.model_name
        _embedder = QueryEmbeddings(model_name=embedding_model)
    return _embedder

def get_client():
    """
    Defining Qdrant cient connection using singleton pattern
    """
    global _client 
    if _client is None: 
        _client = QdrantClient(
            host=settings.qdrant.host,
            port=settings.qdrant.port
        )
    return _client

'''should recreate this function to work properly 
unless select_by_condition func throw unexpected result'''

# def clean_value(val: Any) -> Any:

#     if isinstance(val, str):
#         return val.strip().replace("\n", " ")
#     if val is None or isinstance(val, (bool,int,float)):
#         return val
#     return str(val)

def generate_description(props: PlotProperties) -> str:
    """
    Generates a natural language description for land plot based on its attributes.

    This function parses a dictionary of properties to construct a formatted summary 
    for subsequent vectorization.

    Args:
        props(Dict[str,Any]): dictionary with plot metadata
        Expected keys:
            - 'square' (float/str): The are of the plot in hectares.
            - 'propriet' (str): The type of ownership or legal right.
            - 'provided' (str): How the plot can be acquired.
            - 'Electricit' (str): A string "True" if there is any power supplies.
            - 'Water' (str): A string "True" if there is any water supplies.
            - 'Gas' (str): A string "True" is there is any gas supplies.
            - 'restrict' (str): Describtion of any restrictions of the plot.
    
    Returns:
        str: A concatenated strig of sentences describing the plot.
        Returns "Земельный участок" if the input dictionary is empty
        or contains no matching keys.
    """
    parts = []

    if props.square:
        parts.append(f"Площадь участка: {props.square} га.")

    if props.propriet:
        parts.append(f"Право: {props.propriet}.")

    if props.provide:
        parts.append(f"Получен: {props.provide}.")

    if props.Electricit == "True":
        parts.append("Есть электроснабжение.")
    
    if props.Water == "True":
        parts.append("Есть водоснабжение.")
    
    if props.Gas == "True":
        parts.append("Есть газоснабжение")

    if props.restrict:
        parts.append(f"Ограничения: {props.restrict}.")

    if not parts:
        parts.append("Земельный участок.")
    print(" ".join(parts))
    return " ".join(parts)