from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.schemas.user import UserProfileUpdate, PasswordChange
from app.auth import get_password_hash, verify_password
from app.exceptions import NotFoundException, DatabaseException


async def get_user_profile(db: AsyncSession, user_id: int):
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("Пользователь не найден")
        user_dict = user.__dict__.copy()
        user_dict['photo_url'] = user.img.path if hasattr(user, 'img') and user.img else None
        user_dict['organization'] = user.organization.name if hasattr(user, 'organization') and user.organization else None
        user_dict['position'] = user.position.name if hasattr(user, 'position') and user.position else None
        user_dict['department'] = user.department.name if hasattr(user, 'department') and user.department else None
        user_dict['phone_number'] = user.phone_number
        user_dict['thumbnail_url'] = user.thumbnail.path if hasattr(user, 'thumbnail') and user.thumbnail else None
        user_dict.pop('img', None)
        user_dict.pop('img_id', None)
        user_dict.pop('organization_id', None)
        user_dict.pop('position_id', None)
        user_dict.pop('department_id', None)
        return user_dict
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных профиля")


async def update_user_profile(db: AsyncSession, user_id: int, profile: UserProfileUpdate) -> User:
    try:
        result = await db.execute(select(User).filter(User.id == user_id))
        existing_user = result.scalar_one_or_none()
        if not existing_user:
            raise NotFoundException("Пользователь не найден")

        update_data = profile.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(existing_user, key, value)

        await db.commit()
        await db.refresh(existing_user)
        # Возвращаем профиль в нужном формате (как get_user_profile)
        user_dict = existing_user.__dict__.copy()
        user_dict['photo_url'] = existing_user.img.path if hasattr(existing_user, 'img') and existing_user.img else None
        user_dict['organization'] = existing_user.organization.name if hasattr(existing_user, 'organization') and existing_user.organization else None
        user_dict['position'] = existing_user.position.name if hasattr(existing_user, 'position') and existing_user.position else None
        user_dict['department'] = existing_user.department.name if hasattr(existing_user, 'department') and existing_user.department else None
        user_dict['phone_number'] = existing_user.phone_number
        user_dict['thumbnail_url'] = existing_user.thumbnail.path if hasattr(existing_user, 'thumbnail') and existing_user.thumbnail else None
        user_dict.pop('img', None)
        user_dict.pop('img_id', None)
        user_dict.pop('organization_id', None)
        user_dict.pop('position_id', None)
        user_dict.pop('department_id', None)
        return user_dict
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при обновлении профиля")


async def change_password(db: AsyncSession, user_id: int, password_data: PasswordChange) -> User:
    try:
        existing_user = await get_user_profile(db, user_id)
        if not existing_user:
            raise NotFoundException("Пользователь не найден")

        if not verify_password(password_data.old_password, existing_user.password):
            raise DatabaseException("Неверный текущий пароль")

        existing_user.password = get_password_hash(password_data.new_password)
        await db.commit()
        await db.refresh(existing_user)
        return existing_user
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при изменении пароля") 