# app/auth.py
import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфигурация JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256" # Алгоритм хеширования для JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Время жизни токена в минутах

if not SECRET_KEY:
    raise ValueError("SECRET_KEY не установлен в .env файле. Это необходимо для JWT.")

# Конфигурация для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Схема OAuth2 для получения токена (FastAPI автоматически добавляет в Swagger)
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
    username: Optional[str] = None

# --- Функции для работы с паролями и JWT ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие открытого пароля хешированному."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Хеширует пароль."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT Access Token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15) # Дефолтный срок жизни
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Временная "база данных" пользователей (для простоты тестового) ---
# В реальном приложении это были бы записи в БД
FAKE_USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": get_password_hash("securepassword"), # !!! В реальном приложении хешируйте пароль ОДИН раз при создании пользователя
    }
}
# Убедитесь, что пароль для 'admin' хешируется только один раз
# При первом запуске или если вы меняете пароль вручную здесь,
# убедитесь, что этот хеш генерируется корректно.

async def get_user(username: str) -> Optional[UserInDB]:
    """Получает пользователя из фейковой БД."""
    if username in FAKE_USERS_DB:
        user_dict = FAKE_USERS_DB[username]
        return UserInDB(**user_dict)
    return None

async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Аутентифицирует пользователя по логину и паролю."""
    user = await get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Зависимость FastAPI для получения текущего пользователя из JWT-токена.
    Вызывает HTTPException 401, если токен невалиден.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return User(username=user.username) # Возвращаем объект User без хешированного пароля

# Зависимость для получения АКТИВНОГО пользователя
# (в данном случае "активный" просто означает "аутентифицированный")
async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Возвращает текущего аутентифицированного пользователя."""
    return current_user