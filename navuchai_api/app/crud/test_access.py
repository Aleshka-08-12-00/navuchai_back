from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import secrets

from app.models.test_access import TestAccess
from app.models.user_group_member import UserGroupMember
from app.models.test_access_status import TestAccessStatus
from app.models.test_status import TestStatus
from app.models.test import Test, TestAccessEnum
from app.schemas.test_access import TestAccessCreate
from app.exceptions import DatabaseException, NotFoundException

OPAQUE_TOKEN_NUM_BYTES = 16


def _generate_access_code() -> str:
    return secrets.token_urlsafe(OPAQUE_TOKEN_NUM_BYTES)


async def create_test_access(db: AsyncSession, test_access_data: TestAccessCreate) -> TestAccess:
    """Создание доступа к тесту для одного пользователя"""
    try:
        test_result = await db.execute(select(Test).where(Test.id == test_access_data.test_id))
        test = test_result.scalar_one_or_none()
        if not test:
            raise NotFoundException(f"Тест с ID {test_access_data.test_id} не найден")

        data_for_model = test_access_data.model_dump(exclude_none=True)
        data_for_model.pop('access_code', None)
        db_test_access = TestAccess(**data_for_model)

        if test_access_data.user_id:
            db_test_access.access_code = _generate_access_code()

        db.add(db_test_access)
        await db.commit()
        await db.refresh(db_test_access)
        return db_test_access
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при создании доступа к тесту: {str(e)}")
    except Exception as e:
        raise DatabaseException(f"Неожиданная ошибка при создании доступа к тесту: {str(e)}")


async def create_group_test_access(db: AsyncSession, test_id: int, group_id: int, start_date: datetime = None, end_date: datetime = None, status_id: int = None) -> list[TestAccess]:
    """Создание доступа к тесту для группы пользователей"""
    try:
        if status_id:
            status_result = await db.execute(select(TestStatus).where(TestStatus.id == status_id))
            status = status_result.scalar_one_or_none()
            if not status:
                raise NotFoundException(f"Статус с ID {status_id} не найден")

        query = select(UserGroupMember).where(UserGroupMember.group_id == group_id)
        result = await db.execute(query)
        group_members = result.scalars().all()
        if not group_members:
            raise NotFoundException(f"В группе с ID {group_id} нет пользователей")

        created_accesses = []
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


async def get_test_access(db: AsyncSession, test_id: int, user_id: int) -> TestAccess:
    """Получение информации о доступе пользователя к тесту (по test_id и user_id)"""
    try:
        query = select(TestAccess).where(
            TestAccess.test_id == test_id,
            TestAccess.user_id == user_id
        ).options(selectinload(TestAccess.status))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении информации о доступе к тесту")


async def update_test_access(db: AsyncSession, test_id: int, access: str) -> Test:
    """Изменение значения access в тесте"""
    try:
        if access not in ['public', 'private']:
            raise ValueError("Значение access должно быть 'public' или 'private'")
        query = select(Test).where(Test.id == test_id)
        result = await db.execute(query)
        test = result.scalar_one_or_none()
        if not test:
            raise NotFoundException(f"Тест с ID {test_id} не найден")
        stmt = update(Test).where(Test.id == test_id).values(access=access)
        await db.execute(stmt)
        await db.commit()
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении доступа к тесту")
    except ValueError as e:
        raise DatabaseException(str(e))


async def get_test_access_code(db: AsyncSession, test_id: int, user_id: int) -> dict:
    """Получение кода доступа к тесту"""
    test = await db.execute(select(Test).where(Test.id == test_id))
    test = test.scalar_one_or_none()
    if not test:
        raise NotFoundException(f"Тест с id {test_id} не найден")
    if test.access == TestAccessEnum.PUBLIC:
        return {"code": test.code}
    test_access = await db.execute(select(TestAccess).where(TestAccess.test_id == test_id, TestAccess.user_id == user_id))
    test_access = test_access.scalar_one_or_none()
    if not test_access:
        raise NotFoundException(f"Доступ к тесту {test_id} для пользователя {user_id} не найден")
    return {"access_code": test_access.access_code}


async def update_test_access_status(db: AsyncSession, test_id: int, user_id: int, is_passed: bool) -> TestAccess:
    """Обновление статуса доступа к тесту в зависимости от результата"""
    try:
        test_access = await get_test_access(db, test_id, user_id)
        if not test_access:
            raise NotFoundException(f"Доступ к тесту {test_id} для пользователя {user_id} не найден")
        status_result = await db.execute(
            select(TestAccessStatus).where(TestAccessStatus.code.in_(['COMPLETED', 'FAILED']))
        )
        statuses = {s.code: s for s in status_result.scalars().all()}
        if not statuses:
            raise NotFoundException("Статусы доступа 'COMPLETED' и 'FAILED' не найдены")
        new_status = statuses['COMPLETED'] if is_passed else statuses['FAILED']
        test_access.status_id = new_status.id
        await db.commit()
        await db.refresh(test_access)
        return test_access
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при обновлении статуса доступа: {str(e)}")
