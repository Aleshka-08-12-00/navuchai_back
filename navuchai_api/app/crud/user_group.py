from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload

from app.models import UserGroup, UserGroupMember, User
from app.schemas.user_group import UserGroupCreate, UserGroupUpdate
from app.exceptions import NotFoundException, DatabaseException
from app.models.test_access import TestAccess


async def create_group(db: AsyncSession, group_data: UserGroupCreate, creator_id: int) -> UserGroup:
    try:
        new_group = UserGroup(**group_data.dict(), creator_id=creator_id)
        db.add(new_group)
        await db.commit()
        await db.refresh(new_group)
        await db.refresh(new_group, ['members'])
        return new_group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании группы: {str(e)}")


async def get_group(db: AsyncSession, group_id: int) -> UserGroup:
    result = await db.execute(
        select(UserGroup)
        .options(selectinload(UserGroup.members))
        .where(UserGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise NotFoundException("Группа не найдена")
    return group


async def get_groups(db: AsyncSession) -> list[UserGroup]:
    result = await db.execute(
        select(UserGroup)
        .options(selectinload(UserGroup.members))
    )
    return result.scalars().all()


async def update_group(db: AsyncSession, group_id: int, group_data: UserGroupUpdate) -> UserGroup:
    try:
        group = await get_group(db, group_id)
        for key, value in group_data.dict(exclude_unset=True).items():
            setattr(group, key, value)
        await db.commit()
        await db.refresh(group)
        await db.refresh(group, ['members'])
        return group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении группы: {str(e)}")


async def delete_group(db: AsyncSession, group_id: int) -> UserGroup:
    try:
        group = await get_group(db, group_id)
        # Удаляем все доступы по group_id
        await db.execute(
            TestAccess.__table__.delete().where(TestAccess.group_id == group_id)
        )
        await db.delete(group)
        await db.commit()
        return group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении группы: {str(e)}")


async def add_group_member(db: AsyncSession, group_id: int, user_id: int) -> UserGroupMember:
    try:
        # Проверяем существование группы
        await get_group(db, group_id)

        # Проверяем существование пользователя
        user_result = await db.execute(select(User).where(User.id == user_id))
        if not user_result.scalar_one_or_none():
            raise NotFoundException(f"Пользователь с ID {user_id} не найден")

        member = UserGroupMember(user_id=user_id, group_id=group_id)
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member
    except IntegrityError:
        await db.rollback()
        raise DatabaseException("Пользователь уже состоит в этой группе")
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при добавлении пользователя в группу: {str(e)}")


async def remove_group_member(db: AsyncSession, group_id: int, user_id: int) -> UserGroupMember:
    try:
        await get_group(db, group_id)
        result = await db.execute(
            select(UserGroupMember)
            .where(
                UserGroupMember.group_id == group_id,
                UserGroupMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundException("Пользователь не найден в группе")
        # Удаляем все доступы по group_id и user_id
        await db.execute(
            TestAccess.__table__.delete().where(
                (TestAccess.group_id == group_id) & (TestAccess.user_id == user_id)
            )
        )
        await db.delete(member)
        await db.commit()
        return member
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении пользователя из группы: {str(e)}")


async def is_user_in_group(db: AsyncSession, group_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(UserGroupMember).where(
            UserGroupMember.group_id == group_id,
            UserGroupMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none() is not None