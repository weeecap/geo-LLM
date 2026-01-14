from llama_cpp import Llama

llm = None 
class LLMManager():

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Llama(
                model_path='/Users/dzmitry.mikhasko/Documents/geo-rag/api/Mistral-Nemo-Instruct-2407-Q4_K_S.gguf',
                n_ctx=2048,
                n_gpu_layers=-1,
                verbose=False
            )
        return cls._instance


def generate_response(prompt:list):
    llm = LLMManager.get_instance()

    response_generator = llm.create_chat_completion(
        messages = prompt,
        temperature=0.7, 
    )

    return generate_response["choices"][0]["message"]["content"]


