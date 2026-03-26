from typing import List, Literal, Union, Optional, TypedDict, Dict
from pydantic import BaseModel, ConfigDict

from langchain.messages import AnyMessage
from langgraph.graph import MessagesState
from langmem.short_term import RunningSummary

# ------------------------
# Geometry primitives
# ------------------------

Position = List[float]
"""A single position in [long, lat] format"""

LinearRing = List[Position]
"""A closed linestring: list of positions (points) where last==first"""

PolygonCoords = List[LinearRing]
"""Coordinates of a polygon: [exterior_ring, interior_ring]"""

MultiPolygonCoords = List[PolygonCoords]
"""Coordinates of a MultiPolygon: list of Polygon coordinate arrays"""

# ----------------------------
# GeoJSON Geometry Types
# ----------------------------

class Point(BaseModel):
    """GeoJSON Point geometry"""
    type: Literal["Point"]
    coordinates: Position

class LineString(BaseModel):
    """GeoJSON LineString geometry"""
    type: Literal["LineString"]
    coordinates: LinearRing

class Polygon(BaseModel):
    """GeoJSON Polygon geometry"""
    type: Literal["Polygon"]
    coordinates: PolygonCoords

class MultiPolygon(BaseModel):
    """GeoJSON MultiPolygon geometry"""
    type: Literal["MultiPolygon"]
    coordinates: MultiPolygonCoords

Geometry = Union[Point,LineString,Polygon,MultiPolygon]
"""Union type representibg any kind of GeoJSON geometry"""

# ----------------------------
# Feature Properties
# ----------------------------

class PlotProperties(BaseModel):
    """
    Metadata of land plots feature
    
    Represents attributes of features. 
    All fields except `id` and `square` are optional.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    ownership: Optional[str] = None
    provide: Optional[str] = None 
    restricts: Optional[str] = None
    square:float
    electro: Optional[str] = None
    water: Optional[str] = None
    gas: Optional[str] = None
    email:Optional[str] = None
    link:Optional[str] = None
    district:Optional[str] = None
    coordinates:Optional[dict] = None
    

# ------------------------------
# Coordinate Reference System 
# ------------------------------

class CRSProperties(BaseModel):
    """Properties of coordinate reference system"""
    name: str

class CRS(BaseModel):
    """Coordinates reference system"""
    type: str
    properties: CRSProperties


# -------------------------------
# GeoJSON Feature & Collection
# -------------------------------

class Feature(BaseModel):
    """
    GeoJSON feature representing a single land plot
    """
    type: Literal["Feature"]
    properties: PlotProperties
    geometry: MultiPolygon  # <-- Strict: only MultiPolygon allowed, but can be changed to custom Geometry type


class FeatureCollection(BaseModel):
    """
    GeoJSON FeatureCollection containing multiple land plots
    """
    type: Literal["FeatureCollection"]
    name: Optional[str] = None
    crs: Optional[CRS] = None
    features: List[Feature]

# -------------------------------
# Chat Model
# -------------------------------

class ChatMessage(BaseModel):
    role: str
    content: str 

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str

# ---------------
# LLM Classes
# ---------------

class State(MessagesState):
    context: dict[str, RunningSummary]

class LLMInputState(TypedDict):
    summarized_messages: list[AnyMessage]

# ---------------
# Functions 
# ---------------

class FunctionCall(BaseModel):
    arguments:dict
    """
    The arguments to call the function with, as generate by the model in JSON 
    format. Note that the model does not always generate valid JSON, and may
    hallucinate parametres not defined by function schema. 
    """
    name:str
    """The name of the function to call"""

class FunctionDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, object]] = None

class FunctionSignature(BaseModel):
    function: FunctionDefinition
    type: Literal["function"]