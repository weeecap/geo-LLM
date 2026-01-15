import yaml
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, Any

CONFIG_PATH = Path(__file__).parent / "config.yaml"

def load_yaml_config(path:Path) -> Dict[str, Any]:
    """
    Load and parse a YAML configuration file
    """
    with open(path) as f:
        return yaml.safe_load(f)
    
class QdrantConfig(BaseModel):
    """
    Configuration settings for connecting to a Qdrant vector database instance
    """
    host:str = 'localhost'
    port:int = 6333

class EmbeddingConfig(BaseModel):
    """
    Configuration for text embedding generation and document chunking
    """
    model_name:str = 'intfloat/multilingual-e5-large'
    vector_size:int = 1024
    chunk_size:int = 500
    chunk_overlap:int = 100   

class LLMConfig(BaseModel):
    """
    Configuration for loading and running a local LLM in GGUF 
    """
    model_path: str = "/Users/dzmitry.mikhasko/Documents/geo-rag/api/Mistral-Nemo-Instruct-2407-Q4_K_S.gguf"
    temperature:float = 0.7
    n_ctx:int = 2048
    n_gpu_layers:int = -1
    verbose:bool = False

class Settings(BaseModel):
    """
    Central application configuration container that aggregates all subsystem settings.

    This class combines configurations for Qdrant, embedding models, and the LLM.
    It supports loading from a YAML file (`config.yaml`) or using built-in defaults.
    """
    qdrant:QdrantConfig = QdrantConfig()
    embedding:EmbeddingConfig = EmbeddingConfig()
    llm:LLMConfig = LLMConfig() 

    @classmethod    
    def from_yaml(cls, path:Path=CONFIG_PATH) -> "Settings":
        """
        Create a Settings instance by loading configuration from a YAML file.

        If the specified file exists, it is parsed and used to populate the settings.
        If the file is missing, an instance with default values is returned.

        Args:
            path (Path): Path to the YAML configuration file. Defaults to 'config.yaml'
                in the current module's directory.

        Returns:
            Settings: Fully initialized configuration object.
        """        
        if path.exists():
            data = load_yaml_config(CONFIG_PATH)
            return cls.model_validate(data)
        else:
            return cls()

settings = Settings()