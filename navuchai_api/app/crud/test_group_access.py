from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models.test_group_access import TestGroupAccess
from app.models.user import User
from app.models.user_group import UserGroup
from app.models.test_group import TestGroup
from app.models.test_access_status import TestAccessStatus
from app.schemas.test_group_access import TestGroupAccessCreate, TestGroupAccessUpdate
from app.exceptions import DatabaseException, NotFoundException


async def create_test_group_access(db: AsyncSession, test_group_access: TestGroupAccessCreate) -> TestGroupAccess:
    """Создание доступа к группе тестов"""
    try:
        # Проверяем существование группы тестов
        test_group_result = await db.execute(
            select(TestGroup).where(TestGroup.id == test_group_access.test_group_id)
        )
        test_group = test_group_result.scalar_one_or_none()
        if not test_group:
            raise NotFoundException(f"Группа тестов с ID {test_group_access.test_group_id} не найдена")

        # Проверяем существование пользователя
        user_result = await db.execute(
            select(User).where(User.id == test_group_access.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundException(f"Пользователь с ID {test_group_access.user_id} не найден")

        # Проверяем существование группы пользователей (если указана)
        if test_group_access.user_group_id:
            user_group_result = await db.execute(
                select(UserGroup).where(UserGroup.id == test_group_access.user_group_id)
            )
            user_group = user_group_result.scalar_one_or_none()
            if not user_group:
                raise NotFoundException(f"Группа пользователей с ID {test_group_access.user_group_id} не найдена")

        # Проверяем существование статуса (если указан)
        if test_group_access.status_id:
            status_result = await db.execute(
                select(TestAccessStatus).where(TestAccessStatus.id == test_group_access.status_id)
            )
            status = status_result.scalar_one_or_none()
            if not status:
                raise NotFoundException(f"Статус с ID {test_group_access.status_id} не найден")

        # Проверяем, нет ли уже доступа
        existing_access = await get_test_group_access(
            db, 
            test_group_access.test_group_id, 
            test_group_access.user_id
        )
        if existing_access:
            raise DatabaseException("У пользователя уже есть доступ к этой группе тестов")

        db_test_group_access = TestGroupAccess(**test_group_access.model_dump())
        db.add(db_test_group_access)
        await db.commit()
        await db.refresh(db_test_group_access)
        return db_test_group_access
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании доступа к группе тестов: {str(e)}")


async def get_test_group_access(db: AsyncSession, test_group_id: int, user_id: int) -> TestGroupAccess:
    """Получение доступа к группе тестов"""
    try:
        result = await db.execute(
            select(TestGroupAccess).where(
                TestGroupAccess.test_group_id == test_group_id,
                TestGroupAccess.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении доступа к группе тестов: {str(e)}")


async def update_test_group_access(
    db: AsyncSession, 
    test_group_id: int, 
    user_id: int, 
    test_group_access_update: TestGroupAccessUpdate
) -> TestGroupAccess:
    """Обновление доступа к группе тестов"""
    try:
        test_group_access = await get_test_group_access(db, test_group_id, user_id)
        if not test_group_access:
            raise NotFoundException("Доступ к группе тестов не найден")

        update_data = test_group_access_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(test_group_access, field, value)

        await db.commit()
        await db.refresh(test_group_access)
        return test_group_access
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении доступа к группе тестов: {str(e)}")


async def delete_test_group_access(db: AsyncSession, test_group_id: int, user_id: int) -> bool:
    """Удаление доступа к группе тестов"""
    try:
        test_group_access = await get_test_group_access(db, test_group_id, user_id)
        if not test_group_access:
            raise NotFoundException("Доступ к группе тестов не найден")

        await db.delete(test_group_access)
        await db.commit()
        return True
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении доступа к группе тестов: {str(e)}")


async def get_test_group_accesses_by_user(db: AsyncSession, user_id: int) -> list[TestGroupAccess]:
    """Получение всех доступов к группам тестов для пользователя"""
    try:
        result = await db.execute(
            select(TestGroupAccess).where(TestGroupAccess.user_id == user_id)
        )
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении доступов к группам тестов: {str(e)}")


async def get_test_group_accesses_by_test_group(db: AsyncSession, test_group_id: int) -> list[TestGroupAccess]:
    """Получение всех доступов к группе тестов"""
    try:
        result = await db.execute(
            select(TestGroupAccess).where(TestGroupAccess.test_group_id == test_group_id)
        )
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении доступов к группе тестов: {str(e)}") 