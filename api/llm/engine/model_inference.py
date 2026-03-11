from typing import List
import traceback

from langchain_community.chat_models import ChatLlamaCpp
from langchain_core.runnables import RunnableLambda
from langchain_classic.agents import AgentExecutor
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_qdrant import QdrantVectorStore

from . import functions
from ..settings import settings
from ..utils import logger
from ..prompt.create_prompt import nous_hermes_prompt
from ..agents.base import create_agent
from utils.embedder import EmbeddingManager
from utils.qdrant_client import QdrantManager

class ModelInference():

    _instance: ChatLlamaCpp | None=None
    _retrieval_chain: Runnable | None=None
    _agent_executor: AgentExecutor | None=None

    @classmethod
    def get_instance(cls):
        """
        Create Settings instance from YAML config file.
        """

        if cls._instance is None:
            cls._instance = ChatLlamaCpp(
                model_path=settings.llm.model_path,  
                n_ctx=settings.llm.n_ctx,
                n_gpu_layers=settings.llm.n_gpu_layers,
                verbose=settings.llm.verbose,
                streaming=False,
            )
            logger.info(f"[ModelInference] LLM was initialized {cls._instance}")
        return cls._instance
    
    @classmethod
    def get_retrieval_chain(cls):
        """
        Create retrieval chain for searching through vector db
        """

        if cls._retrieval_chain is not None:
            return cls._retrieval_chain
        
        logger.info("[ModelInference] Initializing retrieval chain")
        client =  QdrantManager.get_instance()
        embedding = EmbeddingManager.get_instance()

        vector_store = QdrantVectorStore(
            client=client,
            collection_name='documents',
            embedding=embedding,
            content_payload_key="page_content",
        )
        
        retriever = vector_store.as_retriever(
            search_type="similarity", 
            search_kwargs={"k":5}
        )

        def rag_pipeline(inputs: dict): 
            query = inputs["input"]
            logger.info(f"[RAG] Incoming query: {query}") 
            docs = retriever.invoke(query)  
            context = "\n\n".join([d.page_content for d in docs])
            logger.info(f"[RAG] Retrieved {len(docs)} docs") 
            return { 
                "input": query, 
                "context": context, 
                "answer": context
            } 
        cls._retrieval_chain = RunnableLambda(rag_pipeline) 
        return cls._retrieval_chain

    @classmethod
    def get_tools(cls) -> List[BaseTool]:
        """
        Return list of instruments as LangChain compatible class
        """    
        return functions.tools
    
    @classmethod
    def get_agent_executor(cls):
        """
        Creating AgentExecutor instnace based on pre-initialized llm 
        """
        if cls._agent_executor is not None:
            return cls._agent_executor
        
        llm = cls.get_instance()
        tools = cls.get_tools()

        tools_dict = [convert_to_openai_function(t) for t in tools]
        logger.info(
            f"[ModelInference] Tools for prompt: {[t['name'] for t in tools_dict]}"
        )

        prompt = nous_hermes_prompt.partial(tools=tools_dict)
        agent = create_agent(
            llm=llm, 
            prompt=prompt
        )

        cls._agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            return_intermediate_steps=True
        )
        logger.info("[ModelInference] AgentExecutor initialized")
        return cls._agent_executor


    @classmethod
    def generate_response(cls, query: str):
        """
        Generate response based on user query using function calling
        """
        try:
            logger.info(f"[ModelInference] New query: {query}")
            agent_executor = cls.get_agent_executor()
            
            inputs = {
                "input": query,
            }
            logger.info(f"[ModelInference] Invoking AgentExecutor with inputs: {inputs}")

            result = agent_executor.invoke(inputs)

            intermediate_steps = result.get("intermediate_steps", [])
            if intermediate_steps:
                logger.info(
                    f"[ModelInference] Intermediate steps count: {len(intermediate_steps)}"
                )
                for i, (action, obs) in enumerate(intermediate_steps, start=1):
                    logger.info(
                        f"[Step {i}] Tool: {getattr(action, 'tool', 'unknown')} | "
                        f"Input: {getattr(action, 'tool_input', {})} | "
                        f"Observation: {obs}"
                    )
            else:
                logger.info("[ModelInference] No intermediate tool calls")

            output = result.get("output", "")
            if isinstance(output, dict) and "response" in output:
                final_text = output["response"]
            elif isinstance(output, str):
                final_text = output
            else:
                final_text = str(output)
            
            final_text = final_text.replace("<|im_end|>", "").strip()

            logger.info(f"[ModelInference] Final output: {final_text}")
            return {"response": final_text}

        except Exception as e:
            logger.error(f"[ModelInference] Error during generation: {e}")
            traceback.print_exc()
            return {"response": f"Ошибка: {str(e)}"}