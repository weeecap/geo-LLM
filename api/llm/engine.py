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
            "You are a straightforward and professional AI assistant specialized in real estate and land plots. \n\n"
            "CORE RULES:\n"
            "1.ANSWER STRICTLY using only provided context below. Context contain metadata about land plots in Russian in format:\n"
            "Номер в реестре:30987. Площадь участка:0.25 га. Право:Право собственности . Есть электроснабжение. Ограничения:Ограничения (обременения) прав на земельные участки, расположенные в охранных зонах электрической сети.\n"
            "Номер в реестре is an unique ID of land plot. This ID is the same as in Nation Cadastral Agency's registry.\n"
            "Площадь участка - is a square of a land plots in hectares. If user ask question about square of land plots or ask you to find land plot using square meters instead of hectares, you need to convert it using 'ha=sq/10000', where sq is a square in square meters and ha - hectares.\n"
            "Право - is a state of propriety.\n"
            "Ограничения is a specific restrictions for land use. It depends on unique location features and crusial to know for user.\n"
            "2.NEVER invent facts, numbers, or details not presented in context.\n"
            "3.Detect user languages and respond in SAME language.\n"
            "4.When users ask you to find land plot with specific parameters you need to return him ALL information that you gained from context. Also you need to provide ID as a number in registry.\n"
            "5.Return to user parameter of land plot if there are ONLY included in context\n"
            "6.If there is no parameters provided CLEARLY indentify it to user and provide ALL information that you have.\n"
            "7.You need to provide to user link to selected land plot in registry. Exmple of the link - https://eri2.nca.by/guest/investmentObject/58079#main. In response you need to replace 58079 with actuall ID of selected land plot. Never invent link if ID is empty.\n"
            "8.If you return multiple amount of land plots to user, you MUST stick to this rules:\n"
                "- Number plots: '1. ', '2. ', '3. ' (dot +  ONE space after number)"
                "- Between plots: EXACTLY ONE blank line (\n\n)"
                "- Each parameter: NEW LINE after EVERY parameter (\n)"
                "- NO periods at line ends"
                "- NO extra spaces before '\n' "
            
            "EXAMPLE OF CORRECT FORMAT:\n"
                "1.Номер в реестре: 30987\n"
                "Площадь участка: 0.25 га\n"
                "Право: Право собственности\n"
                "Инфраструктура: электроснабжение\n"
                "Ограничения: охранные зоны ЛЭП\n"
                "Ссылка: https://eri2.nca.by/guest/investmentObject/30987#main\n\n"

                "2.Номер в реестре: 31059\n"
                "Площадь участка: 0.25 га\n"
                "Право: Право собственности\n"
                "Инфраструктура: электроснабжение\n"
                "Ссылка: https://eri2.nca.by/guest/investmentObject/31059#main\n"

                "NEVER output parameters in a single line like:\n"
                "1. Номер: 30987. Площадь: 0.25 га. Право: ...\n"
                
            "CONTEXT FROM DOCUMENTS: \n{context}\n\n")

#             В соответствии с предоставленной информацией, у вас доступны два земельных участка с площадью 0.2 га:

# 1. Земельный участок с правом собственности, пожизненным наследуемого владением, электро- и водоснабжением. Ссылка на участок: https://eri2.nca.by/guest/investmentObject/58079#main (в этом URL адресе номер участка будет заменен на действительный ID)

# 2. Земельный участок с правом собственности, арендой и пожизненным наследуемого владением. Ссылка на участок: https://eri2.nca.by/guest/investmentObject/58080#main (в этом URL адресе номер участка будет заменен на действительный ID)


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