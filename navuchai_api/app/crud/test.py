from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload

from app.models import Test, Category, User, Locale, File, TestStatus
from app.schemas.test import TestCreate
from app.utils import format_test_with_names
from app.exceptions import NotFoundException, DatabaseException


# Получение списка тестов
async def get_tests(db: AsyncSession):
    try:
        result = await db.execute(
            select(Test, Category.name, User.name, Locale.code, TestStatus.name, TestStatus.name_ru, TestStatus.color)
            .join(Category, Test.category_id == Category.id)
            .join(User, Test.creator_id == User.id)
            .join(Locale, Test.locale_id == Locale.id)
            .join(TestStatus, Test.status_id == TestStatus.id)
            .options(selectinload(Test.image))
        )
        rows = result.all()
        return [format_test_with_names(test, category_name, creator_name, locale_code, status_name, status_name_ru, status_color)
                for test, category_name, creator_name, locale_code, status_name, status_name_ru, status_color in rows]
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка тестов")


# Получение конкретного теста по ID
async def get_test(db: AsyncSession, test_id: int):
    try:
        result = await db.execute(
            select(Test, Category.name, User.name, Locale.code, TestStatus.name, TestStatus.name_ru, TestStatus.color)
            .join(Category, Test.category_id == Category.id)
            .join(User, Test.creator_id == User.id)
            .join(Locale, Test.locale_id == Locale.id)
            .join(TestStatus, Test.status_id == TestStatus.id)
            .options(selectinload(Test.image))
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
        select(Test)
        .options(selectinload(Test.image))
        .where(Test.id == test_id)
    )
    return result.scalar_one_or_none()


# Создание нового теста
async def create_test(db: AsyncSession, test_data: TestCreate):
    try:
        # Проверяем существование связанных сущностей
        category_result = await db.execute(
            select(Category).where(Category.id == test_data.category_id)
        )
        category = category_result.scalar_one_or_none()
        if not category:
            raise NotFoundException(f"Категория с ID {test_data.category_id} не найдена")

        status_result = await db.execute(
            select(TestStatus).where(TestStatus.id == test_data.status_id)
        )
        status = status_result.scalar_one_or_none()
        if not status:
            raise NotFoundException(f"Статус с ID {test_data.status_id} не найдена")

        locale_result = await db.execute(
            select(Locale).where(Locale.id == test_data.locale_id)
        )
        locale = locale_result.scalar_one_or_none()
        if not locale:
            raise NotFoundException(f"Локаль с ID {test_data.locale_id} не найдена")

        # Получаем создателя теста
        creator_result = await db.execute(
            select(User).where(User.id == test_data.creator_id)
        )
        creator = creator_result.scalar_one_or_none()
        if not creator:
            raise NotFoundException(f"Пользователь с ID {test_data.creator_id} не найден")

        # Если указан img_id, проверяем существование файла
        if test_data.img_id:
            file_result = await db.execute(
                select(File).where(File.id == test_data.img_id)
            )
            file = file_result.scalar_one_or_none()
            if not file:
                raise NotFoundException(f"Файл с ID {test_data.img_id} не найден")

        new_test = Test(**test_data.dict())
        db.add(new_test)
        await db.commit()
        await db.refresh(new_test)

        # Форматируем ответ с дополнительными данными
        return format_test_with_names(
            new_test,
            category.name,
            creator.name,
            locale.code,
            status.name,
            status.name_ru,
            status.color
        )
    except IntegrityError as e:
        await db.rollback()
        error_msg = str(e.orig)
        if "foreign key constraint" in error_msg.lower():
            raise DatabaseException("Ошибка при создании теста: нарушение внешнего ключа. Проверьте существование связанных сущностей.")
        elif "unique constraint" in error_msg.lower():
            raise DatabaseException("Ошибка при создании теста: нарушение уникального ограничения.")
        else:
            raise DatabaseException(f"Ошибка при создании теста: {error_msg}")
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании теста: {str(e)}")


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
