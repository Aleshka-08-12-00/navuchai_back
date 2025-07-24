from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from app.models.test_group import TestGroup
from app.models.test_group_test import TestGroupTest
from app.schemas.test_group import TestGroupCreate, TestGroupUpdate
from app.schemas.test_group_test import TestGroupTestCreate
from app.exceptions import DatabaseException, NotFoundException
from app.models import Test, Category, User, Locale, TestStatus
from app.utils import format_test_with_names

# Получение списка всех групп
async def get_test_groups(db: AsyncSession):
    try:
        stmt = select(TestGroup)
        result = await db.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении списка групп: {str(e)}")

# Получение одной группы
async def get_test_group(db: AsyncSession, group_id: int):
    try:
        stmt = select(TestGroup).where(TestGroup.id == group_id)
        result = await db.execute(stmt)
        group = result.scalar_one_or_none()
        if not group:
            raise NotFoundException("Группа не найдена")
        return group
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении группы: {str(e)}")

# Создание группы
async def create_test_group(db: AsyncSession, group: TestGroupCreate):
    try:
        db_group = TestGroup(**group.dict())
        db.add(db_group)
        await db.commit()
        await db.refresh(db_group)
        return db_group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании группы: {str(e)}")

# Обновление группы
async def update_test_group(db: AsyncSession, group_id: int, group: TestGroupUpdate):
    try:
        db_group = await get_test_group(db, group_id)
        for field, value in group.dict(exclude_unset=True).items():
            setattr(db_group, field, value)
        await db.commit()
        await db.refresh(db_group)
        return db_group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении группы: {str(e)}")

# Удаление группы
async def delete_test_group(db: AsyncSession, group_id: int):
    try:
        db_group = await get_test_group(db, group_id)
        await db.delete(db_group)
        await db.commit()
        return db_group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении группы: {str(e)}")

# Добавление теста в группу
async def add_test_to_group(db: AsyncSession, data: TestGroupTestCreate):
    try:
        db_link = TestGroupTest(**data.dict())
        db.add(db_link)
        await db.commit()
        await db.refresh(db_link)
        return db_link
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при добавлении теста в группу: {str(e)}")

# Получение тестов по group_id с полной инфой (возврат ORM-объектов для TestWithDetails)
async def get_tests_by_group_id(db: AsyncSession, group_id: int):
    try:
        stmt = (
            select(
                Test, Category.name, User.name, Locale.code, 
                TestStatus.name, TestStatus.name_ru, TestStatus.color
            )
            .join(Category, Test.category_id == Category.id)
            .join(User, Test.creator_id == User.id)
            .join(Locale, Test.locale_id == Locale.id)
            .join(TestStatus, Test.status_id == TestStatus.id)
            .join(TestGroupTest, Test.id == TestGroupTest.test_id)
            .where(TestGroupTest.test_group_id == group_id)
            .options(selectinload(Test.image))
            .options(selectinload(Test.thumbnail))
        )
        result = await db.execute(stmt)
        rows = result.all()
        # Собираем объекты, совместимые с TestWithDetails
        tests = []
        for test, category_name, creator_name, locale_code, status_name, status_name_ru, status_color in rows:
            test.category_name = category_name
            test.creator_name = creator_name
            test.locale_code = locale_code
            test.status_name = status_name
            test.status_name_ru = status_name_ru
            test.status_color = status_color
            tests.append(test)
        return tests
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении тестов группы: {str(e)}") 