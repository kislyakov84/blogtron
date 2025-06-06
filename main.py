# main.py
from fastapi import FastAPI
from app.database import database, create_db_tables
from app.models import posts # Это нужно, чтобы metadata знала о таблице 'posts'
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager # <-- Добавляем этот импорт

# Загружаем переменные окружения
load_dotenv()

# Определяем lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Функция, управляющая жизненным циклом приложения.
    Выполняется при запуске и завершении работы приложения.
    """
    print("Starting up...")
    create_db_tables() # Создаем таблицы при старте приложения
    await database.connect() # Подключаемся к базе данных
    yield # Код до yield выполняется при запуске
    print("Shutting down...")
    await database.disconnect() # Код после yield выполняется при завершении

app = FastAPI(
    title="Telegram Blog Bot API",
    description="API for managing blog posts for a Telegram bot.",
    version="0.0.1",
    lifespan=lifespan # <-- Указываем FastAPI использовать наш lifespan
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Telegram Blog Bot API!"}

if __name__ == "__main__":
    import uvicorn
    # Вместо прямого объекта 'app', передаем строку "module_name:app_object_name"
    # Это позволяет Uvicorn правильно использовать reload=True
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)