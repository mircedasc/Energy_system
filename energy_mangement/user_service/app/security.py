from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from jose import JWTError, jwt
import os

# Acestea TREBUIE să fie identice cu cele din auth_service
SECRET_KEY = os.getenv("SECRET_KEY", "un-secret-foarte-sigur-default")
ALGORITHM = "HS256"

# Aici se specifică URL-ul de unde se obține token-ul (la API Gateway)
# Chiar dacă e în alt serviciu, FastAPI trebuie să știe calea
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None


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

        if username is None or role is None:
            raise credentials_exception

        return {"username": username, "role": role}

    except JWTError:
        raise credentials_exception


# Dependință pentru a verifica dacă utilizatorul este Administrator
async def require_admin_role(user_data: dict = Depends(get_current_user_data)):
    if user_data.get("role") != "Administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted. Admin role required."
        )
    return user_data