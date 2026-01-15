from llama_cpp import Llama
from settings import settings

class LLMManager():

    _instance = None

    @classmethod
    def get_instance(cls):
        """Create Settings instance from YAML config file."""
        if cls._instance is None:
            cls._instance = Llama(
                model_path=settings.llm.model_path,
                n_ctx=settings.llm.n_ctx,
                n_gpu_layers=settings.llm.n_gpu_layers,
                verbose=settings.llm.verbose
            )
        return cls._instance

def generate_response(prompt:list):
    """
    Generate a response using the loaded LLM.

    Args:
        prompt: List of chat messages in OpenAI format:
                [{"role": "user", "content": "..."}, ...]

    Returns:
        Generated text content.
    """
    llm = LLMManager.get_instance()

    response = llm.create_chat_completion(
        messages=prompt,
        temperature=settings.llm.temperature, 
    )

    return response["choices"][0]["message"]["content"]


