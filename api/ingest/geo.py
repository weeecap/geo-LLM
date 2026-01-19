import json
from typing import Dict, Any, List

from qdrant_client.http import models
from qdrant_client.models import VectorParams, Distance

from shapely.geometry import shape
from shapely.errors import ShapelyError

from schemas import FeatureCollection
from settings import settings
from utils import (
    logger, 
    get_client, 
    get_embedder, 
    generate_description
    )

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
        logger.error("Pydantic FeatureCollection validation failed: %s", e)
        return {
            "status":"error",
            "message":"Pydantic FeatureCollection validation failed"
        }
    
    embedder = get_embedder()
    client = get_client()

    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    logger.info("Creating collection '%s' with vector size %d and COSINE distance.", collection_name, VECTOR_SIZE)
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=VECTOR_SIZE, 
            distance=Distance.COSINE
        )
    )

    points: List[models.PointStruct] = []
    features = collection.features

    for feature in features:
        plot_id = feature.properties.id
        props = feature.properties or {}
        
        geom = feature.geometry
        if not geom:
            logger.warning("Skipping feature %s: missing geometry", plot_id)
            continue
        try:
            geom_dict = feature.geometry.model_dump()
            shapely_geom = shape(geom_dict)
            
            if not shapely_geom.is_valid:
                shapely_geom = shapely_geom.buffer(0)
            
            centroid = shapely_geom.centroid
            
        except (ShapelyError, Exception) as e:
            logger.warning("Skipping feature %s: geometry error - %s", plot_id, e)
            continue  

        description = generate_description(props)
        vector = embedder.embed_query(description)  
        payload = feature.properties.model_dump()

        payload["description"] = description
        payload["geometry"] = json.dumps(feature.geometry.model_dump(), ensure_ascii=False)
        payload["location"] = {"lon": float(centroid.x), "lat": float(centroid.y)}

        point = models.PointStruct(
            id=plot_id,
            vector=vector,
            payload=payload
        )
        points.append(point)

    logger.info("Uploading %d points to collection '%s'...", len(points), collection_name)
    client.upload_points(
        collection_name=collection_name,
        points=points,
        wait=True  
    )

    return {
        "status": "success",
        "collection_name": collection_name,
        "total_features": len(features),
        "ingested_points": len(points),
        "message": f"Successfully ingested {len(points)} land plots into '{collection_name}'."
    }
