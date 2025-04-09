from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Test, Category, User
from app.schemas.test import TestCreate


# Получение списка тестов
async def get_tests(db: AsyncSession):
    result = await db.execute(
        select(Test, Category.name, User.name)
        .join(Category, Test.category_id == Category.id)
        .join(User, Test.creator_id == User.id)
    )
    rows = result.all()

    return [
        {
            "id": test.id,
            "title": test.title,
            "description": test.description,
            "time_limit": test.time_limit,
            "category_id": test.category_id,
            "category_name": category_name,
            "creator_id": test.creator_id,
            "creator_name": creator_name,
            "access_timestamp": test.access_timestamp,
            "status": test.status,
            "frozen": test.frozen,
            "locale": test.locale,
            "created_at": test.created_at,
            "updated_at": test.updated_at
        }
        for test, category_name, creator_name in rows
    ]


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
