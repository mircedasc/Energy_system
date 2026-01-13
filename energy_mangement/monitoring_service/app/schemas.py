from pydantic import BaseModel
from typing import List

class ConsumptionBase(BaseModel):
    timestamp: int
    total_consumption: float

class ConsumptionRecord(ConsumptionBase):
    id: int
    device_id: int

    class Config:
        from_attributes = True