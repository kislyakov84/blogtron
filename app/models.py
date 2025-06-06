# app/models.py
from sqlalchemy import Table, Column, Integer, String, DateTime
from app.database import metadata # Импортируем metadata из database.py
import datetime

# Определение таблицы Post
posts = Table(
    "posts",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("title", String, index=True),
    Column("text", String),
    Column("created_at", DateTime, default=datetime.datetime.now),
)