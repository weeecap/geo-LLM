import logging
from .schemas import PlotProperties, FeatureCollection, Feature
from typing import Optional, Dict, Any
from shapely.geometry import shape
from shapely.errors import ShapelyError

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.INFO,
)

def generate_description(props: Dict[str, Any]) -> str:  
    """
    Generates a natural language description for land plot based on its attributes.

    This function parses a dictionary of properties to construct a formatted summary 
    for subsequent vectorization.

    Args:
        props(Dict[str,Any]): dictionary with plot metadata
        Expected keys:
            - 'id' (int): Identifier of land plot as in national cadatral agency.
            - 'district' (str): Ditrict in which land plot located.
            - 'square' (float): The are of the plot in hectares.
            - 'ownership' (str): The type of ownership or legal right.
            - 'provided' (str): How the plot can be acquired.
            - 'electro' (str): A string "True" if there is any power supplies.
            - 'water' (str): A string "True" if there is any water supplies.
            - 'gas' (str): A string "True" is there is any gas supplies.
            - 'restricts' (str): Describtion of any restrictions of the plot.
            - 'email' (str): Email of responsible organization.
            - 'link' (str): Link to the plot in national cadastral agency.

    Returns:
        str: A concatenated string of sentences describing the plot.
        Returns "Земельный участок" if the input dictionary is empty
        or contains no matching keys.
    """
    parts = []

    if props.get("id"):
        parts.append(f"Номер в реестре: {props['id']}.")

    if props.get("district"):
        parts.append(f"Участок в {props['district']}.")

    if props.get("square"):
        parts.append(f"Площадь участка: {props['square']} га.")

    if props.get("ownership"):
        parts.append(f"Возможный вид права: {props['ownership']}.")

    if props.get("provide"):
        parts.append(f"Предоставляется {props['provide']}.")

    if props.get("electro") == "True":
        parts.append("Есть электроснабжение.")
    
    if props.get("water") == "True":
        parts.append("Есть водоснабжение.")
    
    if props.get("gas") == "True":
        parts.append("Есть газоснабжение.")

    if props.get("restricts"):
        parts.append(f"Ограничения: {props['restricts']}.")

    if props.get("email"):
        parts.append(f"Электронная почта: {props['email']}")
    
    if props.get("link"):
        parts.append(f"Ссылка на участок в НКА: {props['link']}")

    if props.get("coordinates"):
        c = props["coordinates"]
        parts.append(f"Координаты участка: {c['lat']:.6f}, {c['lon']:.6f}.")

    if not parts:
        parts.append("Земельный участок.")

    return " ".join(parts)


def prepare_data(feature: Feature) -> Optional[Dict[str, Any]]:
    """
    Готовит данные из одной Feature для индексации.
    Возвращает dict с свойствами + вычисленным центроидом,
    или None, если геометрия невалидна.
    """
    
    props: Dict[str, Any] = {}

    try:
        props = feature.properties.model_dump() if feature.properties else {}
        plot_id = props.get("id")
        
        if not feature.geometry:
            logger.warning("Feature %s: missing geometry", plot_id)
            return None
            
        geom_dict = feature.geometry.model_dump()
        shapely_geom = shape(geom_dict)
        
        if not shapely_geom.is_valid:
            shapely_geom = shapely_geom.buffer(0)
            
        centroid = shapely_geom.centroid
        centroid_lon, centroid_lat = float(centroid.x), float(centroid.y)
        
        props["coordinates"] = {"lon": centroid_lon, "lat": centroid_lat}
        
        return props
        
    except (ShapelyError, ValueError, TypeError, AttributeError) as e:
        logger.warning("Feature %s: preparation failed - %s", props.get("id"), e)
        return None
