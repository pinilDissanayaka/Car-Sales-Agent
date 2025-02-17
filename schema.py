from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    username:str
    message: str

class ChatResponse(BaseModel):
    response: str


class RegisterRequest(BaseModel):
    username: str
    email:str