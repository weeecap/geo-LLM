from langchain.agents import create_agent
from langchain_community.chat_models import ChatLlamaCpp
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_qdrant import QdrantVectorStore

from settings import settings
from tools import retrieve_context
from utils import logger, get_client, get_embedder

_RAG_CHAIN = None

class LLMManager():

    _instance: ChatLlamaCpp | None=None
    _retrieval_chain = None

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
    def get_retrieval_chain(cls):
        """Create retrieval chain for searching through vector db"""
        if cls._retrieval_chain is None:
            client =  get_client()
            embedding = get_embedder()

            vector_store = QdrantVectorStore(
                client=client,
                collection_name='document',
                embedding=embedding,
                content_payload_key="text"
            )
            
            retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k":5})
            
            llm = cls.get_instance()


            system_instructions = (
            "Ты — профессиональный ассистент по поиску информации в документации.\n"
            "Используй контекст из документов только если вопрос требует контекса. \n"
            "Отвечай ТОЛЬКО на русском языке, используя предоставленный контекст.\n"
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
        if msg.get("role") == "user":
            query = msg["content"]
            logger.info(f"Query - {query}")
            break
    
    if not query:
        return "Question is not defined"

    try:
        agent = LLMManager.get_retrieval_chain()
        logger.info(f"Agent type: {type(agent)}")

        try:
            response = agent.invoke({"input": query})
            logger.info(f"Response {response}")
            return response["answer"] 
        
        except Exception as e:
            logger.error(f"Error: {e}")
            return "Generation issue."

    except Exception as e:
        logger.error(f"RAG issue: {e}")
        return "An error occured while response processing"

