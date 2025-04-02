import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Загружаем переменные окружения из .env
load_dotenv()

# Читаем DATABASE_URL из окружения
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан в .env файле!")

# Создаём движок SQLAlchemy
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаём сессию
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
