from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import User, Role
from app.schemas.user import UserUpdate
from app.exceptions import NotFoundException, DatabaseException


async def get_users(db: AsyncSession):
    try:
        result = await db.execute(select(User).join(User.role))
        return result.scalars().unique().all()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка пользователей")


async def get_user(db: AsyncSession, user_id: int):
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("Пользователь не найден")
        return user
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных пользователя")


async def update_user(db: AsyncSession, user_id: int, user: UserUpdate):
    try:
        existing_user = await get_user(db, user_id)
        if not existing_user:
            raise NotFoundException("Пользователь не найден")

        update_data = user.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(existing_user, key, value)

        await db.commit()
        await db.refresh(existing_user)
        return existing_user
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при обновлении данных пользователя")


async def delete_user(db: AsyncSession, user_id: int):
    try:
        user = await get_user(db, user_id)
        if not user:
            raise NotFoundException("Пользователь не найден")

        await db.delete(user)
        await db.commit()
        return user
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при удалении пользователя")


async def update_user_role(db: AsyncSession, user_id: int, role_code: str):
    try:
        # Найти роль по коду
        role_result = await db.execute(select(Role).where(Role.code == role_code))
        role = role_result.scalar_one_or_none()
        if not role:
            raise NotFoundException("Роль не найдена")

        # Найти пользователя
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundException("Пользователь не найден")

        # Обновить роль
        user.role_id = role.id
        await db.commit()
        await db.refresh(user)
        return user
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при обновлении роли пользователя")
