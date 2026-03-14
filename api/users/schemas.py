from pydantic import BaseModel, ConfigDict, Field

class User(BaseModel):
    model_config=ConfigDict(from_attributes=True, extra='ignore')

    id:int
    nickname: str = Field(..., min_length=1, max_length=50, description='Nickname')
    password: str = Field(exclude=True)

class Registration(BaseModel):
    model_config=ConfigDict(from_attributes=True, extra='ignore')

    id:int 
    nickname: str = Field(..., min_length=1, max_length=50, description="User's nickname")
    password: str = Field(..., min_length=5, max_length=30, description='Password, no less than 5 symbols')


    