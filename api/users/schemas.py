from pydantic import BaseModel, ConfigDict, Field

class User(BaseModel):
    model_config=ConfigDict(from_attributes=True, extra='ignore')

    id:int
    name:str = Field(min_length=1, max_length=25, description="Имя")
    surname:str = Field(min_length=1, max_length=50, description="Фамилия")
    