from langchain.tools import tool 
from typing import Optional
import math

from .geo_matching.geocoding import geocode
from ..utils import logger

@tool
def retrieve_context(query:str):
    """
    Retrieve information about relevant land plot from Qdrant vector store to help find right plot to user
    Args:
        query: Natural language question about land plots, zoning, or infrastructure.
    Returns:
        str: Answer text 
    """

    from .model_inference import ModelInference

    logger.info(f'retrieve_context called with: {query}')
    if not isinstance(query, str) or not query.strip():
        return "Ошибка: некорректный запрос. Требуется строка на русском языке."
    
    try:
        retriever = ModelInference.get_retrieval_chain()
    except Exception as e:
        logger.error(f"[retrieve_context] Failed to load retrieval chain: {e}") 
        return "Ошибка: не удалось инициализировать поисковую систему."
    
    try:
        response = retriever.invoke({"input": query}) 
        answer = response.get("answer", "").strip()

        if not answer:
            return "По вашему запросу ничего не найдено"
        
        logger.info(f'Context from docs is {answer}')

        return answer
    
    except Exception as e:
        logger.error(f"[retrieve_context] RAG execution error: {e}") 
        return "Ошибка: не удалось выполнить поиск по базе данных."
    
@tool
def orthodromic_distance(
        location:str, 
        plot_coords:dict, 
        R:int = 6378160
        ):
    """
    Calculate orthodromic distance between two points - land plot and point of user's interest - using haversine formula.

    Args:
        - location: point of interest, provided by user in query.
        - plot_coords: coordinates of retrieved land plot in format {'lat':latitude, 'lon':longitude}.
        - R: the Earth's mean radius in meters. Constant value for haversine calculations.
    Return:
        - distance between two points in meters 
    """

    location_coords = geocode(location)
    logger.info(f'Coordinates of {location}:{location_coords}')

    if not location_coords:
        return f"Не удалось получить координаты для {location}"
    
    lat_1, lon_1 = math.radians(location_coords['lat']), math.radians(location_coords['lon'])
    lat_2, lon_2 = math.radians(plot_coords['lat']), math.radians(plot_coords['lon'])

    dlat = lat_2 - lat_1
    dlon = lon_2 - lon_1

    a = math.sin(dlat/2)**2 + math.cos(lat_1) * math.cos(lat_2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    distance = (R * c)/1000
    logger.info(f"Distance from land plot to POI {distance}")

    return distance

tools = [retrieve_context, orthodromic_distance]
