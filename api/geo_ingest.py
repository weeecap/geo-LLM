import json
import logging
import uuid
import os
from typing import Any, Dict, List

from qdrant_client.http import models
from qdrant_client.models import VectorParams, Distance

from shapely.geometry import shape
from shapely.errors import ShapelyError

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from schemas import FeatureCollection
from utils import (
    get_client, 
    get_embedder, 
    generate_description, 
    VECTOR_SIZE
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='logs.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
        # Extract properties (metadata) — may be None, so default to empty dict
        plot_id = feature.properties.id
        props = feature.properties or {}
        
        # Extract geometry — skip if missing
        geom = feature.geometry
        if not geom:
            logger.warning("Skipping feature %s: missing geometry", plot_id)
            continue
        try:
            # Convert Pydantic geometry to dict if needed (for shapely)
            geom_dict = feature.geometry.model_dump()
            shapely_geom = shape(geom_dict)
            
            # Attempt to fix invalid geometries (common with real-world data)
            if not shapely_geom.is_valid:
                shapely_geom = shapely_geom.buffer(0)
            
            # Compute centroid (representative point for geospatial queries)
            centroid = shapely_geom.centroid
            
        except (ShapelyError, Exception) as e:
            logger.warning("Skipping feature %s: geometry error - %s", plot_id, e)
            continue  # Skip malformed geometries

        # Generate a natural language description from properties (for embedding)
        description = generate_description(props)
        
        # Convert description text into a dense vector embedding
        vector = embedder.encode(description).tolist()  # .tolist() for JSON serialization

        # Build payload (metadata stored in Qdrant alongside vector)
        payload = feature.properties.model_dump()

        # Add derived fields to payload:
        #   - Full description (for display or RAG context)
        payload["description"] = description
        payload["geometry"] = json.dumps(feature.geometry.model_dump(), ensure_ascii=False)
        payload["location"] = {"lon": float(centroid.x), "lat": float(centroid.y)}

        # Create a Qdrant point with unique ID, vector, and payload
        # Note: Using index `idx` as ID — consider using a stable ID (e.g., from props) in production
        point = models.PointStruct(
            id=plot_id,
            vector=vector,
            payload=payload
        )
        points.append(point)

    # Upload all processed points to Qdrant in a single batch (efficient)

    logger.info("Uploading %d points to collection '%s'...", len(points), collection_name)
    client.upload_points(
        collection_name=collection_name,
        points=points,
        wait=True  # Wait until data is persisted
    )

    # Return success response with stats
    return {
        "status": "success",
        "collection_name": collection_name,
        "total_features": len(features),
        "ingested_points": len(points),
        "message": f"Successfully ingested {len(points)} land plots into '{collection_name}'."
    }

def ingest_doc(file_path:str, collection_name:str) -> dict:
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
    embedder = get_embedder()
    client = get_client()

    try:
        loader = PyPDFLoader(file_path)
        document = loader.load()
        if not document:
            return {"status": "error", "message": "No content extracted from PDF"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to load PDF: {str(e)}"}    


    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=30,
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

    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
        size=VECTOR_SIZE, 
        distance=Distance.COSINE)
    )

    points = []
    source_name = os.path.basename(file_path)  

    for i, doc in enumerate(texts):
        try:
            vector = embedder.encode(doc.page_content).tolist()

            payload = {
                "text":doc.page_content,
                "source":source_name,
                "page": doc.metadata.get("page", None),
                "chunk_index": i
            }

            point_id = str(uuid.uuid4()) 

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            )
        except Exception as e:
            logger.info(f"Skipping chunk {i} due to embedding error: {e}")
            continue

    if not points:
        return {"status": "error", "message": "No valid chunks to ingest"}

    client.upload_points(
        collection_name=collection_name,
        points=points,
        wait=True
    )

    return {
        "status": "success",
        "collection_name": collection_name,
        "total_chunks": len(texts),
        "ingested_points": len(points),
        "message": f"Successfully ingested {len(points)} chunks from '{file_path}' into '{collection_name}'."
    }

def update_doc(file_path:str, collection_name:str) -> dict:

    embedder = get_embedder()
    client = get_client()

    if not client.collection_exists(collection_name):
        logger.error("Collection '%s' does not exist. Cannot update.", collection_name)
        return {
            "status":"error",
            "message":f"Collection with name '{collection_name}' does not exist"
        }
    
    try:
        loader = PyPDFLoader(file_path)
        document = loader.load()
        if not document:
            return {"status": "error", "message": "No content extracted from PDF"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to load PDF: {str(e)}"} 

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=30,
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
    points = []
    source_name = os.path.basename(file_path)  

    for i, doc in enumerate(texts):
        try:
            vector = embedder.encode(doc.page_content).tolist()

            payload = {
                "text":doc.page_content,
                "source":source_name,
                "page": doc.metadata.get("page", None),
                "chunk_index": i
            }

            point_id = str(uuid.uuid4())

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            )
        except Exception as e:
            logger.info(f"Skipping chunk {i} due to embedding error: {e}")
            continue
    if points:
        logger.info("Upserting %d points into collection '%s'...", len(points), collection_name)
        client.upsert(
            collection_name=collection_name,
            points=points, 
            wait=True)
    else:
        logger.warning("No valid points to upsert into collection '%s'", collection_name)

    return {
        "status": "success",
        "collection_name": collection_name,
        "ingested_points": len(points),
        "message": f"Successfully upsert {len(points)} into '{collection_name}'."
    }

def update_feature(
        geojson_data:Dict[str,Any],
        collection_name:str
) -> dict:
    '''
    Perfroms the insert + update action on specified points into an existed Qdrant collection. 
    Any points with existed id will be overwritten. Useful for incremental updates.

    Args:
        geojson_data (Dict[str, Any]): GeoJSON FeatureCollection
        collection_name (str): Target Qdrant collection (must exist)

    Returns:
        dict: Result dictionary with status and counts
    '''
    try:
        collection = FeatureCollection(**geojson_data)
    except Exception as e:
        logger.error("Pydantic validation failed during update: %s", e)
        return {
            "status":"error",
            "message":"Pydantic validation failed"
        }
    
    embedder = get_embedder()
    client = get_client()

    if not client.collection_exists(collection_name):
        logger.error("Collection '%s' does not exist. Cannot update.", collection_name)
        return {
            "status":"error",
            "message":f"Collection with name '{collection_name}' does not exist"
        }
    
    points: List[models.PointStruct] = []
    features = collection.features

    for feature in features:
        point_id = feature.properties.id
        props = feature.properties or {}
        
        geom = feature.geometry
        if not geom:
            logger.warning("Skipping feature %s: missing geometry", point_id)
            continue

        try:
            geom_dict = feature.geometry.model_dump()
            shapely_geom = shape(geom_dict)
            
            if not shapely_geom.is_valid:
                shapely_geom = shapely_geom.buffer(0)
            
            centroid = shapely_geom.centroid
            
        except (ShapelyError, Exception) as e:
            logger.warning("Skipping feature %s: geometry error - %s", point_id, e)
            continue  

        description = generate_description(props)
        
        vector = embedder.encode(description).tolist()

        payload = feature.properties.model_dump()

        payload["description"] = description
        payload["geometry"] = json.dumps(feature.geometry.model_dump(), ensure_ascii=False)
        payload["location"] = {"lon": float(centroid.x), "lat": float(centroid.y)}


        point = models.PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )
        points.append(point)

    if points:
        logger.info("Upserting %d points into collection '%s'...", len(points), collection_name)
        client.upsert(
            collection_name=collection_name,
            points=points, 
            wait=True)
    else:
        logger.warning("No valid points to upsert into collection '%s'", collection_name)

    return {
        "status": "success",
        "collection_name": collection_name,
        "total_features": len(features),
        "ingested_points": len(points),
        "message": f"Successfully upsert {len(points)} land plots into '{collection_name}'."
    }

def collection_delete(collection_name:str) -> dict:
    '''
    Deletes Qdrant collection if it exist.

    Args: 
        collection_name(str): Name of the collection to delete
    
    Returns:
        dict: Succes confirmation message.
    '''
    client = get_client()

    if client.collection_exists(collection_name):
        logger.info("Deleting collection '%s'", collection_name)
        client.delete_collection(collection_name)
        message = f"'{collection_name}' was successfully deleted"
    else:
        logger.info("Collection '%s' does not exist; nothing to delete", collection_name)
        message = f"'{collection_name}' does not exist"
    
    return {
        "status": "success",
        "collection_name": collection_name,
        "message": message
    }

def select_by_condition(collection_name:str, key:str, value:Any) -> dict:
    '''
    Retrieves all points from specific Qdrant collection matching a metadata condition.

    Performs paginated scroll to fetch all matching records. 
    Useful for filtering land plots by categorical attributes.

    Args:
        collection_name(str): Target collection name 
        key(str): Metadata field name 
        value(Any): Value to match exactly

    Returns:
        dict: Contains status, count, and list of matching points (ID + payload)        
    '''
    client = get_client()

    if not client.collection_exists(collection_name):
        logger.error("Collection '%s' does not exist", collection_name)
        return {
            "status":"error",
            "message":f"Collection with name '{collection_name}' is not exist"
        }
    
    offset=None
    all_points=[]
    logger.info("Scrolling collection '%s' for points where %s == %s", collection_name, key, value)
   
    while True:
        points, next_offset=client.scroll(
            collection_name=collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                ]
            ),
            with_payload=True,
            with_vectors=False,
            limit=1000,
            offset=offset
        )

        for point in points:
            all_points.append({
                "id":point.id,
                "payload":point.payload
            })
        
        offset=next_offset
        if next_offset is None:
            break

    logger.info("Found %d points in collection '%s' matching %s=%s", len(all_points), collection_name, key, value)
    return {
        "status":"success",
        "count":len(all_points),
        "points":all_points
    }

def retrieve_point(collection_name:str, point_id:int) -> dict:

    client = get_client()

    if not client.collection_exists(collection_name):
        logger.error("Collection '%s' does not exist", collection_name)
        return {
            "status":"error",
            "message":f"Collection with name '{collection_name}' is not exist"
        }

    offset = None
    result=[]

    while True:
        point, next_offset=client.scroll(
            collection_name=collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="id",
                        match=models.MatchValue(value=point_id)
                    )
                ]
            ),
            with_payload=True,
            with_vectors=False,
            limit=1000,
            offset=offset
        )
        for point in point:
            result.append({
                "payload":point.payload
            })

        offset=next_offset
        if next_offset is None:
            break

    return {
        "status":"success",
        "points":result
    }
