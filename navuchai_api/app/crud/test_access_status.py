from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.test_access_status import TestAccessStatus
from app.schemas.test_access_status import TestAccessStatusCreate
from app.exceptions import DatabaseException, NotFoundException


async def get_test_access_statuses(db: AsyncSession):
    """Получение всех статусов доступа к тесту"""
    try:
        result = await db.execute(select(TestAccessStatus))
        return result.scalars().all()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении статусов доступа к тесту")


async def get_test_access_status(db: AsyncSession, status_id: int):
    """Получение статуса доступа к тесту по ID"""
    try:
        result = await db.execute(
            select(TestAccessStatus).where(TestAccessStatus.id == status_id)
        )
        status = result.scalar_one_or_none()
        if not status:
            raise NotFoundException("Статус доступа не найден")
        return status
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении статуса доступа к тесту")


async def create_test_access_status(db: AsyncSession, status: TestAccessStatusCreate):
    """Создание нового статуса доступа к тесту"""
    try:
        db_status = TestAccessStatus(**status.model_dump())
        db.add(db_status)
        await db.commit()
        await db.refresh(db_status)
        return db_status
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при создании статуса доступа к тесту")


async def update_test_access_status(db: AsyncSession, status_id: int, status: TestAccessStatusCreate):
    """Обновление статуса доступа к тесту"""
    try:
        db_status = await get_test_access_status(db, status_id)
        for key, value in status.model_dump(exclude_unset=True).items():
            setattr(db_status, key, value)
        await db.commit()
        await db.refresh(db_status)
        return db_status
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при обновлении статуса доступа к тесту")


async def delete_test_access_status(db: AsyncSession, status_id: int):
    """Удаление статуса доступа к тесту"""
    try:
        db_status = await get_test_access_status(db, status_id)
        await db.delete(db_status)
        await db.commit()
        return db_status
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при удалении статуса доступа к тесту") 