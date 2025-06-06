# app/auth.py
import os
from datetime import datetime, timedelta
from typing import Optional  # Optional здесь все еще нужен для expires_delta

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Загружаем переменные окружения
load_dotenv()

# Конфигурация JWT
_SECRET_KEY = os.getenv("SECRET_KEY")
if not _SECRET_KEY:
    raise ValueError("SECRET_KEY не установлен в .env файле. Это необходимо для JWT.")

SECRET_KEY: str = _SECRET_KEY

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Конфигурация для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схема OAuth2 для получения токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# --- Pydantic модели для пользователей ---
class User(BaseModel):
    username: str


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str  # <-- ИЗМЕНЕНО: теперь просто str


# --- Функции для работы с паролями и JWT ---


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- Временная "база данных" пользователей (для простоты тестового) ---
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("securepassword"),
    }
}


async def get_user(username: str) -> Optional[UserInDB]:
    if username in FAKE_USERS_DB:
        user_dict = FAKE_USERS_DB[username]
        return UserInDB(**user_dict)
    return None


async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = await get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise credentials_exception

        if not isinstance(username, str):  # Это хорошая runtime-проверка
            raise credentials_exception

        token_data = TokenData(username=username)  # Теперь username здесь - str
        # Pylance теперь увидит, что token_data.username - это str
    except JWTError:
        raise credentials_exception
    user = await get_user(
        token_data.username
    )  # <-- Pylance больше не будет ругаться здесь
    if user is None:
        raise credentials_exception
    return User(username=user.username)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
