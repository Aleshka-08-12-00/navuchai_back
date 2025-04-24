from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.models import Test, Category, User
from app.schemas.test import TestCreate
from app.utils import format_test_with_names
from app.exceptions import NotFoundException, DatabaseException


# Получение списка тестов
async def get_tests(db: AsyncSession):
    try:
        result = await db.execute(
            select(Test, Category.name, User.name)
            .join(Category, Test.category_id == Category.id)
            .join(User, Test.creator_id == User.id)
        )
        rows = result.all()
        return [format_test_with_names(test, category_name, creator_name) for test, category_name, creator_name in rows]
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка тестов")


# Получение конкретного теста по ID
async def get_test(db: AsyncSession, test_id: int):
    try:
        result = await db.execute(
            select(Test, Category.name, User.name)
            .join(Category, Test.category_id == Category.id)
            .join(User, Test.creator_id == User.id)
            .filter(Test.id == test_id)
        )
        row = result.one_or_none()
        if not row:
            raise NotFoundException("Тест не найден")
        return format_test_with_names(*row)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных теста")


async def get_test_by_id(db: AsyncSession, test_id: int):
    result = await db.execute(
        select(Test).where(Test.id == test_id)
    )
    return result.scalar_one_or_none()


# Создание нового теста
async def create_test(db: AsyncSession, test_data: TestCreate):
    new_test = Test(**test_data.dict())
    db.add(new_test)
    try:
        await db.commit()
        await db.refresh(new_test)
        return new_test
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при создании теста")


# Удаление теста
async def delete_test(db: AsyncSession, test_id: int):
    try:
        test = await get_test_by_id(db, test_id)
        if not test:
            raise NotFoundException("Тест не найден")

        await db.delete(test)
        await db.commit()
        return test
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при удалении теста")


# async def update_test(db: AsyncSession, test_id: int, test: TestUpdate):
#     try:
#         existing_test = await get_test(db, test_id)
#         if not existing_test:
#             raise NotFoundException("Тест не найден")
#
#         update_data = test.dict(exclude_unset=True)
#         for key, value in update_data.items():
#             setattr(existing_test, key, value)
#
#         await db.commit()
#         await db.refresh(existing_test)
#         return existing_test
#     except SQLAlchemyError:
#         await db.rollback()
#         raise DatabaseException("Ошибка при обновлении теста")
