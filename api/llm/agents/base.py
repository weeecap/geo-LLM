from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough

from llm.agents.scratchpad import format_function_message
from llm.agents.output_functions_parser import OutputFunctionsParser


def create_agent(llm: BaseLanguageModel, prompt: ChatPromptTemplate) -> Runnable:
    """
    Create an agent with tool call support 

    Args:
        llm: LLM to use as an agent 
        prompt: the prompt to use 
    
    Returns:
        A Runnable sequence representing an agent. 
        It return either an AgentAction or AgentFinish
    """

    if "agent_scratchpad" not in (
        prompt.input_variables + list(prompt.partial_variables)
    ):
        raise ValueError(
            "Prompt must have input variable `agent_scratchpad`, but wasn't found. "
            f"Found: {prompt.input_variables}"
        )

    agent = (
        RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_function_message(
                x.get("intermediate_steps", [])
            )
        )
        | prompt
        | llm
        | OutputFunctionsParser()
    )

    return agent
