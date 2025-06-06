# app/models.py
import datetime

from sqlalchemy import Column, DateTime, Integer, String, Table

from app.database import metadata  # Импортируем metadata из database.py

# Определение таблицы Post
posts = Table(
    "posts",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("title", String, index=True),
    Column("text", String),
    Column("created_at", DateTime, default=datetime.datetime.now),
)
