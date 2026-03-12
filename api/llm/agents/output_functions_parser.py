import re
from typing import List, Union

from langchain_core.agents import AgentAction, AgentActionMessageLog, AgentFinish
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, Generation
from langchain_classic.agents.agent import AgentOutputParser

from llm.agents.utils import parse_tool_call, check_tool_call

class OutputFunctionsParser(AgentOutputParser):
    """
    Parses a message into agent action/finish.

    Is meant to be used with Nouse Hermes 2 Pro model due to specific 
    function_call parameter to convey what tool to use.

    If a function_call parameter is passed, then that is used to get the tool 
    and tool input.

    If one is not passed, then the AIMessage is assumed to be the final output.
    """

    @property
    def _type(self) -> str:
        return "self-hosted-functions-agent"
    
    @staticmethod
    def _parse_ai_message(message: BaseMessage):
        """
        Parse an AI message
        """
        
        if not isinstance(message, AIMessage):
            raise TypeError(f"Expected an AI message got {type(message)}")
        
        actions = []

        pattern = re.compile(r"<tool_call>(.*?)</tool_call>", re.DOTALL)
        
        content = message.content or ""
        if not isinstance(content, str):
            content = str(content)
            
        try:
            raw_calls = pattern.findall(content)
            tool_calls = [parse_tool_call(t.strip()) for t in raw_calls]
        except Exception as e:
            raise OutputParserException(
                f"Could not parse tool calls from message content: {message.content}. Please ensure that the tool calls are valid JSON. Error: {str(e)}"
            )
        
        if not tool_calls:
            return AgentFinish(
                return_values={"output": str(message.content)}, 
                log=str(message.content)
            )
        

        first_tool_call = tool_calls[0]
        tool_name, tool_input = check_tool_call(first_tool_call)
        content_msg = f"\n{message.content}\n" if message.content else "\n"
        log = f"Invoking: '{tool_name}' with '{tool_input}'\n{content_msg}\n"
        
        return AgentActionMessageLog(
            tool=tool_name,
            tool_input=tool_input,
            log=log,
            message_log=[message]
        )

    def parse_result(self, result: List[Generation], *, partial: bool = False) -> Union[AgentAction, AgentFinish]:
        if not result:
            raise ValueError("Empty result list provided to parse_result")
        
        first_item = result[0]
        
        if isinstance(first_item, ChatGeneration):
            message = first_item.message
            return self._parse_ai_message(message)
        elif isinstance(first_item, AIMessage):
            return self._parse_ai_message(first_item)
        elif isinstance(first_item, BaseMessage):
            return self._parse_ai_message(first_item)
        else:
            if hasattr(first_item, 'message'):
                message = getattr(first_item, 'message')
                if isinstance(message, BaseMessage):
                    return self._parse_ai_message(message)
            raise ValueError(f"This output parser received unexpected input type: {type(first_item)}. Expected ChatGeneration, AIMessage, or BaseMessage.")

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        message = AIMessage(content=text)
        return self._parse_ai_message(message)