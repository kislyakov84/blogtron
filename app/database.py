# app/database.py
import os

from databases import Database
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine

# Загружаем переменные окружения из .env файла
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blog.db")  # Default for safety

# SQLAlchemy Engine (для создания таблиц)
engine = create_engine(DATABASE_URL)

# Метадата для определения таблиц
metadata = MetaData()

# databases Database (для асинхронных операций с FastAPI)
database = Database(DATABASE_URL)


# Функция для создания всех таблиц, определенных в metadata
def create_db_tables():
    metadata.create_all(engine)
