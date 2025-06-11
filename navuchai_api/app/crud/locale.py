from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.locale import Locale
from app.exceptions import DatabaseException


async def get_locales(db: AsyncSession) -> list[Locale]:
    try:
        result = await db.execute(select(Locale))
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении списка локалей: {str(e)}")
