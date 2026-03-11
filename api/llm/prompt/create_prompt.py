import yaml
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, MessagesPlaceholder

current_dir = Path(__file__).resolve().parent

yaml_path = current_dir / "prompt.yaml"

with open(yaml_path, "r", encoding="utf-8") as yaml_file:
    prompt = yaml.safe_load(yaml_file)

sys_msg_template: str = prompt["sys_msg"]
human_msg_template: str = prompt["human_msg"]

nous_hermes_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(sys_msg_template),
    HumanMessagePromptTemplate.from_template(human_msg_template),
    MessagesPlaceholder(variable_name = "agent_scratchpad")
])