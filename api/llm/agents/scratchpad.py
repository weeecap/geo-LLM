import json 
from typing import List, Sequence, Tuple

from langchain_core.agents import AgentAction, AgentActionMessageLog
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

def convert_agent_action_to_messages(
        agent_action: AgentAction, 
        observation: str
    ) -> List[BaseMessage]:

    """
    Convert an agent action to a message. 

    Args:
        agent_action: Agent action to convert.

    Returns:
        AIMessage that corresponds to the original tool invocation.
    """

    messages = []

    # 1. Добавляем оригинальный <tool_call>
    if hasattr(agent_action, "message_log"):
        messages.extend(agent_action.message_log)

    # 2. Добавляем <tool_response> в AIMessage
    tool_response_json = json.dumps(
        {"name": agent_action.tool, "content": observation},
        ensure_ascii=False
    )

    messages.append(
        AIMessage(
            content=f"<tool_response>\n{tool_response_json}\n</tool_response>"
        )
    )

    return messages

    return messages

def create_function_message(
        agent_action: AgentAction, 
        observation: str
    ) -> str:

    """
    Convert agent action and observation into a function message.
    
    Args:
        agent_action: the tool invocation request from the agent.
        observation: the result of the tool invocation.
    
    Returns:
        FunctionMessage that corresponds to the original tool invocation.
    """

    if not isinstance(observation, str):
        try:
            content = json.dumps(observation, ensure_ascii=False)
        except Exception:
            content = str(observation)
    else:
        content = observation
    
    tool_response = {
        "name": agent_action.tool,
        "content": content,
    }

    return json.dumps(tool_response)

def format_function_message(
        intermediate_steps: Sequence[Tuple[AgentAction, str]]
    ) -> List[BaseMessage]:

    """
    Convert (AgentAction, tool output) tuples into FunctionMessages.

    Args:
        intermediate_steps: step the llm has taken to date, along with observation.

    Return:
        list of messages to send to the llm for the next prediction.
    """

    messages = []
    for agent_action, observation in intermediate_steps:
        messages.extend(convert_agent_action_to_messages(agent_action, observation))
    return messages