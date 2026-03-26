import json
from typing import Dict, Any, List

from qdrant_client.http import models
from qdrant_client.models import VectorParams, Distance

from llm.schemas import FeatureCollection
from llm.settings import settings
from llm.utils import logger, generate_description, prepare_data
from utils.embedder import EmbeddingManager
from utils.qdrant_client import QdrantManager

VECTOR_SIZE = settings.embedding.vector_size

def ingest_feature(
        geojson_data:Dict[str,Any],
        collection_name:str
) -> dict:
    '''
    Ingests a GeoJSON FeatureCollection into a Qdrant vector collection.

    This function:
      - Validates the input as a proper GeoJSON FeatureCollection using Pydantic.
      - Deletes any existing Qdrant collection with the same name if its exist (full replace strategy).
      - Creates a new Qdrant collection configured for cosine similarity.
      - Processes each feature:
          * Validates and repairs geometry using Shapely.
          * Computes centroid for geospatial filtering.
          * Generates a natural language description from properties.
          * Embeds the description using the configured embedder.
          * Stores metadata, geometry, and centroid in the payload.
      - Uploads all valid features as vector points.

    Note: Uses list index as point ID—consider using a stable identifier (e.g., from properties)
          in production to support true incremental updates.

    Args:
        geojson_data (Dict[str, Any]): GeoJSON-compliant dictionary with "type" and "features".
        collection_name (str): Name of the Qdrant collection to create.

    Returns:
        dict: Result dictionary with status, counts, and message.
    '''
    try:
        collection = FeatureCollection(**geojson_data)
    except Exception as e:
        logger.error("Pydantic validation failed: %s", e)
        return {"status": "error", "message": "Validation failed"}
    
    embedder = EmbeddingManager.get_instance()
    client = QdrantManager.get_instance()

    logger.info("Creating collection '%s' with vector size %d and COSINE distance.", collection_name, VECTOR_SIZE)
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=VECTOR_SIZE, 
                distance=Distance.COSINE
            )
        )

    points: List[models.PointStruct] = []
    for feature in collection.features:
        prepared = prepare_data(feature)

        if not prepared:
            continue
        
        plot_id = prepared.get("id")

        if plot_id is None:
            logger.warning("Skipping feature: missing 'id' in properties")
            continue

        description = generate_description(prepared)
        vector = embedder.embed_query(description)

        payload = prepared.copy()

        payload["page_content"] = description
        payload["geometry"] = json.dumps(feature.geometry.model_dump(), ensure_ascii=False)
        payload["location"] = prepared["coordinates"]

        point = models.PointStruct(
            id=plot_id,
            vector=vector,
            payload=payload
        )
        points.append(point)

    logger.info("Uploading %d points to collection '%s'...", len(points), collection_name)
    client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True  
    )

    return {
        "status": "success",
        "collection_name": collection_name,
        "total_features": len(collection.features),
        "ingested_points": len(points),
        "message": f"Successfully ingested {len(points)} land plots into '{collection_name}'."
    }
