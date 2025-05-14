from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.models.test_access import TestAccess
from app.models.user_group_member import UserGroupMember
from app.models.test_status import TestStatus
from app.schemas.test_access import TestAccessCreate
from app.exceptions import DatabaseException, NotFoundException


async def create_test_access(
    db: AsyncSession,
    test_access: TestAccessCreate
) -> TestAccess:
    """Создание доступа к тесту для одного пользователя"""
    try:
        db_test_access = TestAccess(**test_access.model_dump())
        db.add(db_test_access)
        await db.commit()
        await db.refresh(db_test_access)
        return db_test_access
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании доступа к тесту")


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
            test_access = TestAccessCreate(
                test_id=test_id,
                user_id=member.user_id,
                group_id=group_id,
                start_date=start_date,
                end_date=end_date,
                status_id=status_id
            )
            created_access = await create_test_access(db, test_access)
            created_accesses.append(created_access)

        return created_accesses
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании группового доступа к тесту")


async def get_test_access(
    db: AsyncSession,
    test_id: int,
    user_id: int
) -> TestAccess:
    """Получение информации о доступе пользователя к тесту"""
    try:
        query = select(TestAccess).where(
            TestAccess.test_id == test_id,
            TestAccess.user_id == user_id
        ).options(selectinload(TestAccess.status))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении информации о доступе к тесту") 