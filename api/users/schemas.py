import enum 
from pydantic import BaseModel

class Roles(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Token(BaseModel):
    acces_token:str
    token_type:str

class TokenData(BaseModel):
    nickname:str | None=None