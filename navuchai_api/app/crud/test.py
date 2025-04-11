from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Test, Category, User
from app.schemas.test import TestCreate
from app.utils import format_test_with_names


# Получение списка тестов
async def get_tests(db: AsyncSession):
    result = await db.execute(
        select(Test, Category.name, User.name)
        .join(Category, Test.category_id == Category.id)
        .join(User, Test.creator_id == User.id)
    )
    rows = result.all()
    return [format_test_with_names(test, category_name, creator_name) for test, category_name, creator_name in rows]


# Получение конкретного теста по ID
async def get_test(db: AsyncSession, test_id: int):
    result = await db.execute(
        select(Test, Category.name, User.name)
        .join(Category, Test.category_id == Category.id)
        .join(User, Test.creator_id == User.id)
        .filter(Test.id == test_id)
    )
    row = result.one_or_none()
    if not row:
        return None
    return format_test_with_names(*row)


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
