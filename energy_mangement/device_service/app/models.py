from sqlalchemy import Column, Integer, String, Float
from .database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)  # "Name" din cerințe
    address = Column(String, nullable=False)  # Câmp extra util
    max_hourly_consumption = Column(Float, nullable=False)

    # RELAȚIA CU USER:
    # Nu folosim ForeignKey real către tabela 'users' pentru a păstra
    # microserviciile decuplate. Stocăm doar ID-ul ca un număr.
    owner_id = Column(Integer, nullable=True, index=True)