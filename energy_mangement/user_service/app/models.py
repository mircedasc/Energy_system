from sqlalchemy import Column, Integer, String
from .database import Base


class User(Base):
    __tablename__ = "users"

    # [cite_start]Atribute minime cerute [cite: 30]
    id = Column(Integer, primary_key=True, index=True)
    auth_id = Column(Integer, unique=True, nullable=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # [cite_start]Atribut suplimentar pentru a gestiona rolurile [cite: 25, 26, 27]
    role = Column(String, default="Client", nullable=False)

    # [cite_start]Aici poți adăuga atribute suplimentare [cite: 31]
    # de ex. first_name = Column(String)
    # de ex. last_name = Column(String)