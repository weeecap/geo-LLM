import re
import json
from langchain_core.utils.function_calling import convert_to_openai_function
from llm.engine.functions import tools

def parse_tool_call(call: str):
    call = call.strip()

    args_match = re.search(r'"arguments"\s*:\s*(\{.*\})\s*,\s*"name"', call, re.DOTALL)
    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', call)

    if not name_match:
        return {"arguments": {}, "name": "missing_function_call"}

    name = name_match.group(1)

    if not args_match:
        return {"arguments": {}, "name": name}

    args_str = args_match.group(1)

    arguments = json.loads(args_str)
    return {"arguments": arguments, "name": name}


def check_tool_call(call: dict):
    openai_tools = [convert_to_openai_function(t) for t in tools]

    tool_name = call.get("name")
    arguments = call.get("arguments", {})

    tool_names = [t["name"] for t in openai_tools]
    if tool_name not in tool_names:
        return "handle_tools_error", {"error": {"error": {"name": tool_name}}}

    tool_schema = next(t for t in openai_tools if t["name"] == tool_name)
    expected_args = set(tool_schema["parameters"]["properties"].keys())
    received_args = set(arguments.keys())

    if expected_args != received_args:
        return "handle_tools_error", {
            "error": {
                "error": {
                    "expected": list(expected_args),
                    "received": list(received_args),
                },
                "name": tool_name,
            }
        }

    return tool_name, arguments