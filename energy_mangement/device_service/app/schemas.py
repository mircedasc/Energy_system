from pydantic import BaseModel
from typing import Optional

class DeviceBase(BaseModel):
    description: str
    address: str
    max_hourly_consumption: float

class DeviceCreate(DeviceBase):
    owner_id: Optional[int] = None # Poate fi setat la creare sau asignat ulterior

class DeviceUpdate(BaseModel):
    description: Optional[str] = None
    address: Optional[str] = None
    max_hourly_consumption: Optional[float] = None
    owner_id: Optional[int] = None

class Device(DeviceBase):
    id: int
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True