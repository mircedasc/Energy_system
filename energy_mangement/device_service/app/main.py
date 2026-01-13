from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, database, security
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(root_path="/devices")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CRUD PENTRU ADMIN SI CLIENT ---

@app.get("/", response_model=List[schemas.Device])
def read_devices(
        db: Session = Depends(database.get_db),
        current_user: dict = Depends(security.get_current_user_data)
):
    """
    Logica hibridă:
    - Dacă e Admin: Returnează TOATE dispozitivele.
    - Dacă e Client: Returnează doar dispozitivele LUI.
    """
    if current_user["role"] == "Administrator":
        return db.query(models.Device).all()
    else:
        # Clientul vede doar device-urile unde owner_id == id-ul lui din token
        return db.query(models.Device).filter(models.Device.owner_id == current_user["id"]).all()


# --- OPERAȚII DOAR PENTRU ADMIN (Create, Update, Delete, Mapping) ---

@app.post("/", response_model=schemas.Device)
def create_device(
        device: schemas.DeviceCreate,
        db: Session = Depends(database.get_db),
        admin: dict = Depends(security.require_admin)  # Doar admin
):
    db_device = models.Device(**device.dict())
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


@app.put("/{device_id}", response_model=schemas.Device)
def update_device(
        device_id: int,
        device_update: schemas.DeviceUpdate,
        db: Session = Depends(database.get_db),
        admin: dict = Depends(security.require_admin)
):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Update logic
    update_data = device_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_device, key, value)

    db.commit()
    db.refresh(db_device)
    return db_device


@app.delete("/{device_id}")
def delete_device(
        device_id: int,
        db: Session = Depends(database.get_db),
        admin: dict = Depends(security.require_admin)
):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(db_device)
    db.commit()
    return {"detail": "Device deleted"}