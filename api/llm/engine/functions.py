from langchain.tools import tool 

from ..utils import logger

@tool
def retrieve_context(query:str):
    """
    Retrieve information about relevant land plot from Qdrant vector store to help find right plot to user
    Args:
        query: Natural language question about land plots, zoning, or infrastructure.
    Returns:
        str: Answer text 
    """

    from .model_inference import ModelInference

    logger.info(f'retrieve_context called with: {query}')
    if not isinstance(query, str) or not query.strip():
        return "Ошибка: некорректный запрос. Требуется строка на русском языке."
    
    try:
        retriever = ModelInference.get_retrieval_chain()
    except Exception as e:
        logger.error(f"[retrieve_context] Failed to load retrieval chain: {e}") 
        return "Ошибка: не удалось инициализировать поисковую систему."
    
    try:
        response = retriever.invoke({"input": query}) 
        answer = response.get("answer", "").strip()

        if not answer:
            return "По вашему запросу ничего не найдено"
        
        logger.info(f'Context from docs is {answer}')

        return answer
    
    except Exception as e:
        logger.error(f"[retrieve_context] RAG execution error: {e}") 
        return "Ошибка: не удалось выполнить поиск по базе данных."
    
tools = [retrieve_context]
