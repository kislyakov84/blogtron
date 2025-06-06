# main.py
from fastapi import FastAPI, HTTPException, status, Depends # <-- Добавляем Depends
from fastapi.security import OAuth2PasswordRequestForm # <-- Добавляем для логина
from app.database import database, create_db_tables
from app.models import posts
from app.schemas import PostCreate, PostUpdate, PostResponse
from app.crud import create_post, get_all_posts, get_post, update_post, delete_post
from app.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, Token, get_current_active_user # <-- Добавляем из auth.py
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import List
from datetime import timedelta # <-- Добавляем для расчета срока жизни токена

# Загружаем переменные окружения
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    create_db_tables()
    await database.connect()
    yield
    print("Shutting down...")
    await database.disconnect()

app = FastAPI(
    title="Telegram Blog Bot API",
    description="API для управления постами блога для Telegram бота.",
    version="0.0.1",
    lifespan=lifespan
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Telegram Blog Bot API!"}

# --- API Эндпоинты для постов ---

@app.post("/token", response_model=Token, summary="Получить JWT токен")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Аутентифицирует пользователя и выдает Access Token.
    Используйте 'admin'/'securepassword' для входа.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- API Эндпоинты для постов ---

# Теперь добавляем зависимость current_user: User = Depends(get_current_active_user)
# к эндпоинтам, которые требуют авторизации.
# Для GET-эндпоинтов /posts/ и /posts/{post_id} авторизация не нужна (по ТЗ).
# Но для POST, PUT, DELETE - нужна!

@app.post("/posts/", response_model=PostResponse, status_code=status.HTTP_201_CREATED, summary="Создать новый пост (требуется аутентификация)")
async def create_new_post(post: PostCreate, current_user: dict = Depends(get_current_active_user)): # <-- Добавляем зависимость
    """
    Создает новый пост в блоге.
    - **title**: Заголовок поста (обязательно)
    - **text**: Текст поста (обязательно)
    """
    # current_user содержит информацию об аутентифицированном пользователе,
    # но для тестового задания мы её не используем, просто факт авторизации.
    post_id = await create_post(post)
    created_post = await get_post(post_id)
    if not created_post:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve created post.")
    return created_post

@app.get("/posts/", response_model=List[PostResponse], summary="Получить все посты")
async def read_all_posts(): # <-- Нет зависимости, доступно без авторизации
    """
    Возвращает список всех существующих постов, отсортированных по дате создания.
    """
    return await get_all_posts()

@app.get("/posts/{post_id}", response_model=PostResponse, summary="Получить пост по ID")
async def read_post_by_id(post_id: int): # <-- Нет зависимости, доступно без авторизации
    """
    Возвращает пост по его уникальному идентификатору.
    - **post_id**: ID поста
    """
    post = await get_post(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post

@app.put("/posts/{post_id}", response_model=PostResponse, summary="Обновить существующий пост (требуется аутентификация)")
async def update_existing_post(post_id: int, post: PostUpdate, current_user: dict = Depends(get_current_active_user)): # <-- Добавляем зависимость
    """
    Обновляет заголовок и/или текст существующего поста.
    - **post_id**: ID поста, который нужно обновить
    - **title**: Новый заголовок поста (необязательно)
    - **text**: Новый текст поста (необязательно)
    """
    existing_post = await get_post(post_id)
    if not existing_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    updated_successfully = await update_post(post_id, post)

    updated_post = await get_post(post_id)
    if not updated_post:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated post.")

    return updated_post


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить пост (требуется аутентификация)")
async def delete_existing_post(post_id: int, current_user: dict = Depends(get_current_active_user)): # <-- Добавляем зависимость
    """
    Удаляет пост по его уникальному идентификатору.
    - **post_id**: ID поста, который нужно удалить
    """
    deleted_successfully = await delete_post(post_id)
    if not deleted_successfully:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)