from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware  # CORS
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
import requests  # Pentru sincronizare

from . import models, schemas, database

# Configurare
SECRET_KEY = os.getenv("SECRET_KEY", "un-secret-foarte-sigur-default")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_service:8000/users/")

app = FastAPI(root_path="/auth")

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Setup DB
models.Base.metadata.create_all(bind=database.engine)

# 3. Security Tools
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- RUTE ---

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    """
    Înregistrează un utilizator nou în Auth DB și îl sincronizează cu User DB.
    """
    # 1. Verifică dacă există în Auth DB
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # 2. Hash parola și salvează în Auth DB
    hashed_password = get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 3. SINCRONIZARE: Trimite datele și la User Service
    # Astfel, Admin-ul îl va vedea în listă, iar user-ul va avea profil.
    try:
        requests.post(
            USER_SERVICE_URL,
            json={
                "username": user.username,
                "password": user.password,  # Trimitem parola raw ca user_service sa o hash-uiasca si el
                "role": user.role,
                "auth_id": new_user.id
            },
            timeout=5
        )
    except Exception as e:
        print(f"Sync error with User Service: {e}")
        # Nu oprim înregistrarea dacă sync-ul eșuează, dar e bine de știut.

    return {"message": "User created successfully"}


@app.post("/login", response_model=schemas.Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TOKEN COMPLET (cu ID)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "id": user.id},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}