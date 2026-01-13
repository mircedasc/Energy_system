from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
#from typing import List
from fastapi.middleware.cors import CORSMiddleware
from . import models, schemas, database, security

# Creează tabelele în baza de date (pentru simplitate, la pornire)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(root_path="/users")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Context pentru hash-uirea parolelor
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


# --- Endpoint-uri ---

@app.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """
    Endpoint public pentru înregistrarea unui utilizator nou.
    Implicit, va avea rolul 'Client'.
    """
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)

    # Asigură-te că doar rolul 'Client' este setat la înregistrarea publică
    # sau permite setarea rolului dacă este specificat (ex. un admin creează alt admin)
    # Să rămânem la 'Client' pentru înregistrarea publică.
    db_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role, auth_id=user.auth_id)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- Endpoint-uri protejate pentru ADMIN ---

@app.get("/", response_model=list[schemas.User])
def read_users(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(database.get_db),
        admin_user: dict = Depends(security.require_admin_role)
):
    """
    Obține o listă cu toți utilizatorii. [cite_start]Doar pentru Admin. [cite: 26, 37]
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users


@app.get("/{user_id}", response_model=schemas.User)
def read_user(
        user_id: int,
        db: Session = Depends(database.get_db),
        admin_user: dict = Depends(security.require_admin_role)
):
    """
    Obține detalii despre un utilizator specific, după ID. Doar pentru Admin.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/{user_id}", response_model=schemas.User)
def update_user(
        user_id: int,
        user_update: schemas.UserUpdate,
        db: Session = Depends(database.get_db),
        admin_user: dict = Depends(security.require_admin_role)
):
    """
    Actualizează un utilizator (username, parolă, rol). Doar pentru Admin.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.username:
        db_user.username = user_update.username
    if user_update.password:
        db_user.hashed_password = get_password_hash(user_update.password)
    if user_update.role:
        db_user.role = user_update.role

    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
        user_id: int,
        db: Session = Depends(database.get_db),
        admin_user: dict = Depends(security.require_admin_role)
):
    """
    Șterge un utilizator. Doar pentru Admin.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return None