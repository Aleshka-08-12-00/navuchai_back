from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from app.models.test_status import TestStatus
from app.schemas.test_status import TestStatusResponse
from app.exceptions import DatabaseException


async def get_test_statuses(db: AsyncSession) -> List[TestStatusResponse]:
    """Получение списка всех статусов тестов."""
    try:
        result = await db.execute(select(TestStatus).order_by(TestStatus.id))
        statuses = result.scalars().all()
        return statuses
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка статусов тестов")
