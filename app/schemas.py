# app/schemas.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Базовая схема для поста (общие поля)
class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Заголовок поста")
    text: str = Field(..., description="Текст поста")


# Схема для создания поста (наследует PostBase)
class PostCreate(PostBase):
    pass


# Схема для обновления поста (все поля опциональны)
class PostUpdate(BaseModel):
    title: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Новый заголовок поста"
    )
    text: Optional[str] = Field(None, description="Новый текст поста")


# Схема для ответа API (включает ID и дату создания)
class PostResponse(PostBase):
    id: int = Field(..., description="Уникальный идентификатор поста")
    created_at: datetime = Field(..., description="Дата и время создания поста")

    class Config:
        from_attributes = True  # В старых версиях Pydantic был orm_mode = True
