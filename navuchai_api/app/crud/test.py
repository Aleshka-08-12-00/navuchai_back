from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Test
from app.schemas.test import TestCreate


# Получение списка тестов
async def get_tests(db: AsyncSession):
    result = await db.execute(select(Test))
    return result.scalars().all()


# Получение конкретного теста по ID
async def get_test(db: AsyncSession, test_id: int):
    result = await db.execute(select(Test).filter(Test.id == test_id))
    return result.scalar_one_or_none()


# Создание нового теста
async def create_test(db: AsyncSession, test_data: TestCreate):
    new_test = Test(**test_data.dict())
    db.add(new_test)
    await db.commit()
    await db.refresh(new_test)
    return new_test


# Удаление теста
async def delete_test(db: AsyncSession, test_id: int):
    test = await get_test(db, test_id)
    if test:
        await db.delete(test)
        await db.commit()
    return test
