"""
Утилита для проверки истекших сроков адаптаций
Можно запускать как отдельный скрипт или интегрировать в cron
"""
import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.crud.adaptation import check_expired_adaptations
from app.config import DATABASE_URL

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_deadlines():
    """Проверяет истекшие адаптации"""
    try:
        # Создаем подключение к БД
        engine = create_async_engine(DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as db:
            updated_count = await check_expired_adaptations(db)
            logger.info(f"Проверка завершена. Обновлено адаптаций: {updated_count}")
            return updated_count
            
    except Exception as e:
        logger.error(f"Ошибка при проверке истекших сроков: {str(e)}")
        raise
    finally:
        if 'engine' in locals():
            await engine.dispose()


async def main():
    """Основная функция для запуска проверки"""
    logger.info("Начинаем проверку истекших адаптаций...")
    await check_deadlines()
    logger.info("Проверка завершена")


if __name__ == "__main__":
    asyncio.run(main())
