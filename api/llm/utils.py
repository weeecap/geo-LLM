import logging
import ast
import xml.etree.ElementTree as ET
import json
import re
import os 
from art import text2art

from .schemas import PlotProperties

script_dir  = os.path.dirname(os.path.abspath(__file__))
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.INFO,
)

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

    if props.id:
        parts.append(f"Номер в реестре:{props.id}.")

    if props.square:
        parts.append(f"Площадь участка:{props.square} га.")

    if props.ownership:
        parts.append(f"Право:{props.ownership}.")

    if props.provide:
        parts.append(f"Получен:{props.provide}.")

    if props.Electricity == "True":
        parts.append("Есть электроснабжение.")
    
    if props.Water == "True":
        parts.append("Есть водоснабжение.")
    
    if props.Gas == "True":
        parts.append("Есть газоснабжение.")

    if props.restriction:
        parts.append(f"Ограничения:{props.restriction}.")

    if not parts:
        parts.append("Земельный участок.")
    return " ".join(parts)
