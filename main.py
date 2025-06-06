# main.py
from fastapi import FastAPI, HTTPException, status # <-- Добавляем HTTPException, status
from app.database import database, create_db_tables
from app.models import posts
from app.schemas import PostCreate, PostUpdate, PostResponse # <-- Добавляем схемы
from app.crud import create_post, get_all_posts, get_post, update_post, delete_post # <-- Добавляем CRUD функции
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from typing import List

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

@app.post("/posts/", response_model=PostResponse, status_code=status.HTTP_201_CREATED, summary="Создать новый пост")
async def create_new_post(post: PostCreate):
    """
    Создает новый пост в блоге.
    - **title**: Заголовок поста (обязательно)
    - **text**: Текст поста (обязательно)
    """
    post_id = await create_post(post)
    # После создания, получаем полный объект поста из БД для ответа
    created_post = await get_post(post_id)
    if not created_post: # На случай, если пост не нашелся после создания (маловероятно)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve created post.")
    return created_post

@app.get("/posts/", response_model=List[PostResponse], summary="Получить все посты")
async def read_all_posts():
    """
    Возвращает список всех существующих постов, отсортированных по дате создания.
    """
    return await get_all_posts()

@app.get("/posts/{post_id}", response_model=PostResponse, summary="Получить пост по ID")
async def read_post_by_id(post_id: int):
    """
    Возвращает пост по его уникальному идентификатору.
    - **post_id**: ID поста
    """
    post = await get_post(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post

@app.put("/posts/{post_id}", response_model=PostResponse, summary="Обновить существующий пост")
async def update_existing_post(post_id: int, post: PostUpdate):
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
    if not updated_successfully:
        # Если update_post вернул False, это значит, что никаких изменений не было,
        # или что-то пошло не так, но пост существует.
        # Можно вернуть текущий пост или 304 Not Modified, если запрос был без изменений
        # Для простоты, если изменения не были применены (например, пустой update_data),
        # мы просто вернем текущий пост.
        # Если же post_id не найден, это уже обработано выше.
        pass # Пропускаем, так как HTTPException уже был бы выброшен

    # Получаем обновленный пост для возврата в ответе
    updated_post = await get_post(post_id)
    if not updated_post: # Крайне маловероятно после успешного обновления
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve updated post.")

    return updated_post


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить пост")
async def delete_existing_post(post_id: int):
    """
    Удаляет пост по его уникальному идентификатору.
    - **post_id**: ID поста, который нужно удалить
    """
    deleted_successfully = await delete_post(post_id)
    if not deleted_successfully:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return # HTTP 204 No Content означает, что нет тела ответа

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)