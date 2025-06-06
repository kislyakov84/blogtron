# app/database.py
from sqlalchemy import create_engine, MetaData
from databases import Database
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blog.db") # Default for safety

# SQLAlchemy Engine (для создания таблиц)
engine = create_engine(DATABASE_URL)

# Метадата для определения таблиц
metadata = MetaData()

# databases Database (для асинхронных операций с FastAPI)
database = Database(DATABASE_URL)

# Функция для создания всех таблиц, определенных в metadata
def create_db_tables():
    metadata.create_all(engine)