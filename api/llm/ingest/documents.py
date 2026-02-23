import uuid
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.http import models
from qdrant_client.models import VectorParams, Distance

from llm.settings import settings
from llm.utils import logger

from utils.embedder import EmbeddingManager
from utils.qdrant_client import QdrantManager

VECTOR_SIZE = settings.embedding.vector_size

def ingest_doc(file_path:str, collection_name:str, file_name:str) -> dict:
    """
    Processes a PDF document by extracting its text, splitting it into chunks,
    generating embeddings, and storing the results in a specified Qdrant vector collection.

    This function:
      - Loads the PDF file using PyPDFLoader.
      - Splits the extracted text into overlapping chunks using a recursive character text splitter.
      - Deletes the existing Qdrant collection (if its exist) with the given name and creates a new one.
      - Generates a vector embedding for each text chunk using a pre-configured embedder.
      - Stores each chunk as a point in Qdrant, enriched with metadata (payload) including:
         - The original text
         - Source filename
         - Page number (if available)
         - Chunk index

    Args:
        file_path (str): Absolute or relative path to a PDF file on disk.
                         The file must exist and be a valid PDF document.
        collection_name (str): Name of the Qdrant collection where vectors will be stored.
                               If a collection with this name exists, it will be deleted and recreated.

    Returns:
        dict: A dictionary containing the ingestion result with the following keys:
            - "status" (str): Either "success" or "error".
            - "message" (str): Human-readable description of the outcome.
            - "collection_name" (str, optional): Name of the target collection (on success).
            - "total_chunks" (int, optional): Total number of text chunks generated.
            - "ingested_points" (int, optional): Number of successfully uploaded vector points.
    """
    embedder = EmbeddingManager.get_instance()
    logger.info(f"'{embedder}")
    client = QdrantManager.get_instance()

    try:
        loader = PyPDFLoader(file_path)
        document = loader.load()
        if not document:
            return {"status": "error", "message": "No content extracted from PDF"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to load PDF: {str(e)}"}    


    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.embedding.chunk_size,
        chunk_overlap=settings.embedding.chunk_overlap,
        separators=[
            "\n\n",        
            "\n",          
            ". ",          
            " ",           
            ""             
        ],
        length_function=len,
    )
    
    texts = text_splitter.split_documents(document)
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=VECTOR_SIZE, 
                distance=Distance.COSINE
            )
        )
    try:
        raw_texts = [doc.page_content for doc in texts]
        vectors = embedder.embed_documents(raw_texts)  
    except Exception as e:
        return {"status": "error", "message": f"Embedding generation failed: {str(e)}"}
    
    points = []

    for i, (doc,vector) in enumerate(zip(texts,vectors)):
        try:
            payload = {
                "text": doc.page_content,
                "source": file_name,
                "page": doc.metadata.get("page", None),
                "chunk_index": i
            }
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector, 
                    payload=payload
                )
            )
            logger.info('points was created succesfully')
        except Exception as e:
            logger.info(f"Skipping chunk {i} due to embedding error: {e}")
            continue

    if not points:
        return {"status": "error", "message": "No valid chunks to ingest"}
    
    logger.info("Trying to upsert points")
    client.upsert(
        collection_name=collection_name,
        points=points, 
        wait=True
    )

    logger.info(f"Successfully ingested {len(points)} chunks from '{file_path}' into '{collection_name}'.")
    return {
        "status": "success",
        "collection_name": collection_name,
        "total_chunks": len(texts),
        "ingested_points": len(points),
        "message": f"Successfully ingested {len(points)} chunks from '{file_path}' into '{collection_name}'."
    }