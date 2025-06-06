# app/crud.py
from app.database import database
from app.models import posts
from app.schemas import PostCreate, PostUpdate
from typing import List, Optional
import datetime

# Create (Создание поста)
async def create_post(post: PostCreate) -> int:
    query = posts.insert().values(
        title=post.title,
        text=post.text,
        created_at=datetime.datetime.now()
    )
    return await database.execute(query)

# Read (Получение всех постов)
async def get_all_posts() -> List[dict]:
    query = posts.select().order_by(posts.c.created_at.desc()) # Сортировка по убыванию даты создания
    return await database.fetch_all(query)

# Read (Получение поста по ID)
async def get_post(post_id: int) -> Optional[dict]:
    query = posts.select().where(posts.c.id == post_id)
    return await database.fetch_one(query)

# Update (Обновление поста)
async def update_post(post_id: int, post: PostUpdate) -> bool:
    # Создаем словарь только с теми полями, которые не None (были переданы)
    update_data = {k: v for k, v in post.model_dump(exclude_unset=True).items()} # model_dump для Pydantic v2+
    if not update_data:
        return False # Ничего обновлять не нужно

    query = posts.update().where(posts.c.id == post_id).values(**update_data)
    result = await database.execute(query)
    return result > 0 # Возвращаем True, если пост был обновлен (т.е. был найден и изменен)

# Delete (Удаление поста)
async def delete_post(post_id: int) -> bool:
    query = posts.delete().where(posts.c.id == post_id)
    result = await database.execute(query)
    return result > 0 # Возвращаем True, если пост был удален