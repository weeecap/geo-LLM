from llama_cpp import Llama
from settings import settings
from langgraph.prebuilt import create_react_agent
from langchain.agents import create_agent
from langchain_community.chat_models import ChatLlamaCpp
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents.middleware import wrap_model_call
from tools import retrieve

class LLMManager():

    _instance: ChatLlamaCpp | None=None
    _agent = None

    @classmethod
    def get_instance(cls):
        """Create Settings instance from YAML config file."""
        if cls._instance is None:
            cls._instance = ChatLlamaCpp(
                model_path=settings.llm.model_path,
                n_ctx=settings.llm.n_ctx,
                n_gpu_layers=settings.llm.n_gpu_layers,
                verbose=settings.llm.verbose
            )
        return cls._instance
    
    @classmethod
    def create_agent(cls):
        if cls._agent is None:
            llm = cls.get_instance()        
            system_instructions = (
            "Ты — профессиональный ассистент по поиску информации в документации. "
            "Твоя задача: отвечать на вопросы пользователя, используя данные из инструмента 'retrieve'.\n\n"
            "ПРАВИЛА РАБОТЫ:\n"
            "1. Если вопрос требует данных из документов, ты ОБЯЗАН вызвать функцию 'retrieve'.\n"
            "2. Формируй вызов функции в строгом соответствии с JSON-схемой.\n"
            "3. НЕ ПИШИ финальный ответ от себя, пока не получишь данные от инструмента.\n"
            "4. Когда данные получены, синтезируй ответ на русском языке на основе этих данных.\n"
            "5. Если в документации нет ответа, так и скажи, не выдумывай факты."
        )
            cls._agent = create_agent(
                model=llm,
                tools=[retrieve],
                system_prompt=system_instructions
            )
        return cls._agent
    
# @wrap_model_call
# def dynamic_model_selection():
#     'Choose model based on conversation complexity'
#     pass

def generate_response(prompt:list):
    """
    Generate a response using the loaded LLM.

    Args:
        prompt: List of chat messages in format:
                [{"role": "user", "content": "..."}, ...]

    Returns:
        Generated text content.
    """
    messages=[]
    for msg in prompt:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        else:
            raise ValueError(f"Unknown role: {role}")

    agent = LLMManager.create_agent()

    response = agent.invoke({"messages": messages})

    return response["messages"][-1].content


