from sqlalchemy import Column, Integer, Float, BigInteger
from .database import Base

class HourlyConsumption(Base):
    __tablename__ = "hourly_consumption"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, nullable=False, index=True)
    timestamp = Column(BigInteger, nullable=False) # Timestamp-ul orei (ex: 10:00, 11:00)
    total_consumption = Column(Float, default=0.0)