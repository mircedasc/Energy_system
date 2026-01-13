from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY", "un-secret-foarte-sigur-default")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user_data(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        user_id: int = payload.get("id")

        if username is None or role is None:
            raise credentials_exception

        # Returnăm un dicționar cu toate datele necesare
        return {"username": username, "role": role, "id": user_id}

    except JWTError:
        raise credentials_exception


# Verificare ADMIN
async def require_admin(user_data: dict = Depends(get_current_user_data)):
    if user_data.get("role") != "Administrator":  # Asigură-te că acesta e string-ul salvat în DB
        raise HTTPException(status_code=403, detail="Admin role required")
    return user_data