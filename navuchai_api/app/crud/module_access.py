from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import secrets

from app.models.module_access import ModuleAccess
from app.models.user_group_member import UserGroupMember
from app.models.test_status import TestStatus
from app.models.module import Module, TestAccessEnum
from app.schemas.module_access import ModuleAccessCreate
from app.exceptions import DatabaseException, NotFoundException

OPAQUE_TOKEN_NUM_BYTES = 16


def _generate_access_code() -> str:
    return secrets.token_urlsafe(OPAQUE_TOKEN_NUM_BYTES)


async def create_module_access(db: AsyncSession, access_data: ModuleAccessCreate) -> ModuleAccess:
    try:
        module = await db.scalar(select(Module).where(Module.id == access_data.module_id))
        if not module:
            raise NotFoundException(f"Модуль с ID {access_data.module_id} не найден")

        data = access_data.model_dump(exclude_none=True)
        data.pop('access_code', None)
        db_access = ModuleAccess(**data)

        if access_data.user_id:
            db_access.access_code = _generate_access_code()

        db.add(db_access)
        await db.commit()
        await db.refresh(db_access)
        return db_access
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при создании доступа к модулю: {str(e)}")


async def create_group_module_access(
    db: AsyncSession,
    module_id: int,
    group_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    status_id: int | None = None
) -> list[ModuleAccess]:
    try:
        if status_id:
            status = await db.scalar(select(TestStatus).where(TestStatus.id == status_id))
            if not status:
                raise NotFoundException(f"Статус с ID {status_id} не найден")

        result = await db.execute(select(UserGroupMember).where(UserGroupMember.group_id == group_id))
        members = result.scalars().all()
        if not members:
            raise NotFoundException(f"В группе с ID {group_id} нет пользователей")

        created = []
        for member in members:
            payload = ModuleAccessCreate(
                module_id=module_id,
                user_id=member.user_id,
                group_id=group_id,
                start_date=start_date,
                end_date=end_date,
                status_id=status_id
            )
            created_access = await create_module_access(db, payload)
            created.append(created_access)
        return created
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании группового доступа к модулю")


async def get_module_access(db: AsyncSession, module_id: int, user_id: int) -> ModuleAccess:
    try:
        query = select(ModuleAccess).where(
            ModuleAccess.module_id == module_id,
            ModuleAccess.user_id == user_id
        ).options(selectinload(ModuleAccess.status))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении доступа к модулю")


async def update_module_access(db: AsyncSession, module_id: int, access: str) -> Module:
    try:
        if access not in ['public', 'private']:
            raise ValueError("Значение access должно быть 'public' или 'private'")

        module = await db.scalar(select(Module).where(Module.id == module_id))
        if not module:
            raise NotFoundException(f"Модуль с ID {module_id} не найден")

        await db.execute(update(Module).where(Module.id == module_id).values(access=access))
        await db.commit()
        return await db.scalar(select(Module).where(Module.id == module_id))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении доступа к модулю")
    except ValueError as e:
        raise DatabaseException(str(e))


async def get_module_access_code(db: AsyncSession, module_id: int, user_id: int) -> dict:
    module = await db.scalar(select(Module).where(Module.id == module_id))
    if not module:
        raise NotFoundException(f"Модуль с id {module_id} не найден")

    if module.access == TestAccessEnum.PUBLIC:
        return {"code": module.id}

    access = await db.scalar(select(ModuleAccess).where(
        ModuleAccess.module_id == module_id,
        ModuleAccess.user_id == user_id
    ))
    if not access:
        raise NotFoundException(f"Доступ к модулю {module_id} для пользователя {user_id} не найден")
    return {"access_code": access.access_code}
