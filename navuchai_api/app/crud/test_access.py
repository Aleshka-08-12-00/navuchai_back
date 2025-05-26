from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import uuid
import secrets

from app.models.test_access import TestAccess
from app.models.user_group_member import UserGroupMember
from app.models.test_status import TestStatus
from app.models.test import Test, TestAccessEnum
from app.schemas.test_access import TestAccessCreate
from app.exceptions import DatabaseException, NotFoundException

OPAQUE_TOKEN_NUM_BYTES = 16


def _generate_access_code() -> str:
    return secrets.token_urlsafe(OPAQUE_TOKEN_NUM_BYTES)


async def create_test_access(
        db: AsyncSession,
        test_access_data: TestAccessCreate
) -> TestAccess:
    """Создание доступа к тесту для одного пользователя"""
    try:
        data_for_model = test_access_data.model_dump(exclude_none=True)
        if 'access_code' in data_for_model:
            del data_for_model['access_code']

        db_test_access = TestAccess(**data_for_model)

        if test_access_data.user_id:
            db_test_access.access_code = _generate_access_code()
        else:
            # Если user_id не предоставлен, генерация access_code для него может быть невозможна
            # или должна быть особая логика. Пока оставляем pass.
            pass

        db.add(db_test_access)
        await db.commit()
        await db.refresh(db_test_access)
        return db_test_access
    except SQLAlchemyError as e:
        raise DatabaseException("Ошибка при создании доступа к тесту")
    except Exception as e:
        raise DatabaseException(f"Неожиданная ошибка при создании доступа к тесту: {e}")


async def create_group_test_access(
        db: AsyncSession,
        test_id: int,
        group_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        status_id: int = None
) -> list[TestAccess]:
    """Создание доступа к тесту для группы пользователей"""
    try:
        # Проверяем существование статуса
        if status_id:
            status_result = await db.execute(
                select(TestStatus).where(TestStatus.id == status_id)
            )
            status = status_result.scalar_one_or_none()
            if not status:
                raise NotFoundException(f"Статус с ID {status_id} не найден")

        # Получаем всех пользователей группы
        query = select(UserGroupMember).where(UserGroupMember.group_id == group_id)
        result = await db.execute(query)
        group_members = result.scalars().all()

        if not group_members:
            raise NotFoundException(f"В группе с ID {group_id} нет пользователей")

        created_accesses = []

        # Создаем доступ к тесту для каждого пользователя
        for member in group_members:
            test_access_payload = TestAccessCreate(
                test_id=test_id,
                user_id=member.user_id,
                group_id=group_id,
                start_date=start_date,
                end_date=end_date,
                status_id=status_id
            )
            created_access = await create_test_access(db, test_access_payload)
            created_accesses.append(created_access)

        return created_accesses
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании группового доступа к тесту")


async def get_test_access(
        db: AsyncSession,
        test_id: int,
        user_id: int
) -> TestAccess:
    """Получение информации о доступе пользователя к тесту (по test_id и user_id)
       Это не для валидации access_code. Для валидации нужен будет другой метод,
       который ищет по access_code.
    """
    try:
        query = select(TestAccess).where(
            TestAccess.test_id == test_id,
            TestAccess.user_id == user_id
        ).options(selectinload(TestAccess.status))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении информации о доступе к тесту")


async def update_test_access(
        db: AsyncSession,
        test_id: int,
        access: str
) -> Test:
    """Изменение значения access в тесте"""
    try:
        if access not in ['public', 'private']:
            raise ValueError("Значение access должно быть 'public' или 'private'")

        # Проверяем существование теста
        query = select(Test).where(Test.id == test_id)
        result = await db.execute(query)
        test = result.scalar_one_or_none()
        
        if not test:
            raise NotFoundException(f"Тест с ID {test_id} не найден")

        # Обновляем значение access
        stmt = update(Test).where(Test.id == test_id).values(access=access)
        await db.execute(stmt)
        await db.commit()

        # Получаем обновленный тест
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении доступа к тесту")
    except ValueError as e:
        raise DatabaseException(str(e))


async def get_test_access_code(db: AsyncSession, test_id: int, user_id: int) -> dict:
    """
    Получение кода доступа к тесту:
    - Если тест публичный, возвращает code из таблицы tests
    - Если тест приватный, возвращает access_code из таблицы test_access
    """
    # Получаем тест
    test = await db.execute(
        select(Test).where(Test.id == test_id)
    )
    test = test.scalar_one_or_none()
    
    if not test:
        raise NotFoundException(f"Тест с id {test_id} не найден")
    
    # Если тест публичный, возвращаем его code
    if test.access == TestAccessEnum.PUBLIC:
        return {"code": test.code}
    
    # Если тест приватный, ищем access_code в таблице test_access
    test_access = await db.execute(
        select(TestAccess).where(
            TestAccess.test_id == test_id,
            TestAccess.user_id == user_id
        )
    )
    test_access = test_access.scalar_one_or_none()
    
    if not test_access:
        raise NotFoundException(f"Доступ к тесту {test_id} для пользователя {user_id} не найден")
    
    return {"access_code": test_access.access_code}
