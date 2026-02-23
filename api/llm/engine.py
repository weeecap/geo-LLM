from langchain_community.chat_models import ChatLlamaCpp
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_qdrant import QdrantVectorStore

from .settings import settings
from .utils import logger
from utils.embedder import EmbeddingManager
from utils.qdrant_client import QdrantManager

class LLMManager():

    _instance: ChatLlamaCpp | None=None

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
            logger.info(cls._instance)
            logger.info("LLM was initialize")
        return cls._instance
 
    @classmethod
    def get_retrieval_chain(cls):
        """Create retrieval chain for searching through vector db"""
        client =  QdrantManager.get_instance()
        embedding = EmbeddingManager.get_instance()

        vector_store = QdrantVectorStore(
            client=client,
            collection_name='documents',
            embedding=embedding,
            content_payload_key="page_content",
        )
        
        llm = LLMManager.get_instance()

        retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k":5})
            
        system_instructions = (
            "Ты — профессиональный ассистент по поиску информации в документации.\n"
            "Используй контекст из документов при ответе на вопрос. \n"
            "Отвечай ТОЛЬКО на русском языке, используя предоставленный контекст.\n"
            "На вход тебе подается история чата - отвечай на последний вопрос пользователя, используй остальную информацию в качестве контекста.\n"
            "При генерации ответа добавляй источник, из которого был получен контекст и конкретную страницу.\n"
            "Если в контексте нет информации для ответа — скажи об этом, НЕ выдумывай факты.\n\n"
            "Контекст из документов:\n{context}"
        )
        qa_prompt=ChatPromptTemplate.from_messages([
            ("system", system_instructions),
            ("human","{input}")
        ])

        combine_docs_chain = create_stuff_documents_chain(llm,qa_prompt)
        cls._retrieval_chain = create_retrieval_chain(retriever,combine_docs_chain)

        return cls._retrieval_chain   

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
        if msg.role == "user":
            query = msg.content
            logger.info(f"Query - {query}")
            break
    
    if not query:
        return "Question is not defined"

    try:
        retriever = LLMManager.get_retrieval_chain()
        logger.info(f"Retriever type: {type(retriever)}")

        try:
            response = retriever.invoke({"input": query})
            logger.info(f"Response {response}")
            return response["answer"] 
        
        except Exception as e:
            logger.error(f"Error: {e}")
            return "Generation issue."

    except Exception as e:
        logger.error(f"RAG issue: {e}")
        return "An error occured while response processing"