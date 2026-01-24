from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str=Field(description="username in string",min_length=3,max_length=50)
    password: str=Field(description="password in stirng", min_length=6)

