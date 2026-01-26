from langchain.agents import create_agent
from langchain_classic.chains.combine_documents import create_stuff_documents_chain 
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_community.chat_models import ChatLlamaCpp
from langchain.agents.middleware import wrap_model_call

from settings import settings
from tools import retrieve_context
from utils import logger

_RAG_CHAIN = None

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
                verbose=settings.llm.verbose,
                streaming=True
            )
        return cls._instance
    
    @classmethod
    def get_agent(cls):
        if cls._agent is None:
            llm = cls.get_instance()        
            system_instructions = (
            "Ты — профессиональный ассистент по поиску информации в документации. "
            "Твоя задача: отвечать на вопросы пользователя, используя данные из инструмента 'retrieve_context'.\n\n"
            "ПРАВИЛА РАБОТЫ:\n"
            "1. ИСПОЛЬЗУЙ ТОЛЬКО РУССКИЙ ЯЗЫК"
            "2. Если вопрос требует данных из документов, ты ОБЯЗАН вызвать функцию 'retrieve_context'.\n"
            "3. Формируй вызов функции в строгом соответствии с JSON-схемой.\n"
            "4. НЕ ПИШИ финальный ответ от себя, пока не получишь данные от инструмента.\n"
            "5. Когда данные получены, синтезируй ответ на русском языке на основе этих данных.\n"
            "6. Если в документации нет ответа, так и скажи, не выдумывай факты."
        )
            cls._agent = create_agent(
                model=llm,
                tools=[retrieve_context],
                system_prompt=system_instructions
            )
        return cls._agent
    
# @wrap_model_call
# def dynamic_model_selection():
#     'Choose model based on conversation complexity'
#     pass

# def get_rag_chain():
  
#     global _RAG_CHAIN

#     if _RAG_CHAIN is None:
#         llm = LLMManager.get_instance()
#         retriever = retrieve(k=3)
#         prompt = ChatPromptTemplate.from_messages([
#             ("system", 
#              "Ты — эксперт по градостроительным и земельным нормам Республики Беларусь. "
#              "Ответь на вопросы о градостроительстве и земельным нормам ТОЛЬКО на основе предоставленного контекста. "
#              "Если вопрос не касается этих тем, отвечай как обычно."
#              "Если в контексте нет ответа, скажи: «В доступной документации ответ не найден.»\n\n"
#              "Контекст:\n{context}"
#             ),
#             ("human", "{input}")
#         ])

#         document_chain = create_stuff_documents_chain(llm, prompt)
#         _RAG_CHAIN = create_retrieval_chain(retriever, document_chain)
    
#     return _RAG_CHAIN


def generate_response(messages:list):
    """
    Generate a response using the loaded LLM.

    Args:
        prompt: List of chat messages in format:
                [{"role": "user", "content": "..."}, ...]

    Returns:
        Generated text content.
    """
    query = None

    for msg in messages:
        if msg.get("role") == "user":
            query = msg["content"]
            logger.info(f"Query - {query}")
            break
    
    if not query:
        return "Question is not defined"

    try:
        agent = LLMManager.get_agent()
        logger.info(f"Agent type: {type(agent)}")

        try:
            response = agent.invoke({"messages":messages})
            logger.info(f"Response {response}")
            logger.info(f'{response["messages"][-1].content}')
            return response["messages"][-1].content
        
        except Exception as e:
            logger.error(f"Error: {e}")
            return "Generation issue."

    except Exception as e:
        logger.error(f"RAG issue: {e}")
        return "An error occured while response processing"

