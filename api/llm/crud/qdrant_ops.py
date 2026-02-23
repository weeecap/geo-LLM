from typing import Any
from qdrant_client.http import models

from llm.utils import  logger
from utils.embedder import EmbeddingManager
from utils.qdrant_client import QdrantManager

def collection_delete(collection_name:str) -> dict:
    '''
    Deletes Qdrant collection if it exist.

    Args: 
        collection_name(str): Name of the collection to delete
    
    Returns:
        dict: Succes confirmation message.
    '''
    client = QdrantManager.get_instance()

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
    client = QdrantManager.get_instance()

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

    client = QdrantManager.get_instance()

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