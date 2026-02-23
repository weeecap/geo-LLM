import logging

from .schemas import PlotProperties, MultiPolygon

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='logs.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
        parts.append(f"Площадь участка:{props.square} га.")

    if props.propriet:
        parts.append(f"Право:{props.propriet}.")

    if props.provide:
        parts.append(f"Получен:{props.provide}.")

    if props.Electricit == "True":
        parts.append("Есть электроснабжение.")
    
    if props.Water == "True":
        parts.append("Есть водоснабжение.")
    
    if props.Gas == "True":
        parts.append("Есть газоснабжение.")

    if props.restrict:
        parts.append(f"Ограничения:{props.restrict}.")

    if not parts:
        parts.append("Земельный участок.")
    return " ".join(parts)


