from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.schemas.user import UserProfileUpdate
from app.auth import get_password_hash
from app.exceptions import NotFoundException, DatabaseException


async def get_user_profile(db: AsyncSession, user_id: int) -> User:
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("Пользователь не найден")
        return user
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных профиля")


async def update_user_profile(db: AsyncSession, user_id: int, profile: UserProfileUpdate) -> User:
    try:
        existing_user = await get_user_profile(db, user_id)
        if not existing_user:
            raise NotFoundException("Пользователь не найден")

        update_data = profile.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password"] = get_password_hash(update_data["password"])

        for key, value in update_data.items():
            setattr(existing_user, key, value)

        await db.commit()
        await db.refresh(existing_user)
        return existing_user
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при обновлении профиля") 