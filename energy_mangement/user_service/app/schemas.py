from pydantic import BaseModel
from typing import Optional

# Schema de bază pentru utilizator (câmpuri comune)
class UserBase(BaseModel):
    username: str

# Schema folosită la crearea unui utilizator (primește parola)
class UserCreate(UserBase):
    password: str
    role: Optional[str] = "Client" # Rolul default este Client
    auth_id: Optional[int] = None

# Schema folosită la actualizarea unui utilizator (toate câmpurile sunt opționale)
class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

# Schema folosită la returnarea unui utilizator din API (fără parolă)
class User(UserBase):
    id: int
    auth_id: int | None = None
    role: str

    class Config:
        from_attributes = True # <-- MODIFICARE: În loc de orm_mode = True