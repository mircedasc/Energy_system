from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None
    id: int | None = None

# Schema pentru Înregistrare
class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "Client"