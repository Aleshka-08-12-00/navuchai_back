from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import secrets
import string
from sqlalchemy.orm import selectinload

from app.models import User, Role, Organization, Position, Department
from app.schemas.user import UserUpdate
from app.exceptions import NotFoundException, DatabaseException
from app.auth import get_password_hash
from app.utils.email_service import email_service


async def get_users(db: AsyncSession):
    try:
        result = await db.execute(
            select(User)
            .join(User.role)
            .options(
                selectinload(User.organization),
                selectinload(User.position),
                selectinload(User.department),
                selectinload(User.img)
            )
        )
        users = result.scalars().unique().all()
        # Формируем нужный формат
        user_list = []
        for user in users:
            user_dict = user.__dict__.copy()
            user_dict['photo_url'] = user.img.path if user.img else None
            user_dict['organization'] = user.organization.name if user.organization else None
            user_dict['position'] = user.position.name if user.position else None
            user_dict['department'] = user.department.name if user.department else None
            user_dict['phone_number'] = user.phone_number
            # Удаляем лишние поля
            user_dict.pop('img', None)
            user_dict.pop('img_id', None)
            user_dict.pop('organization_id', None)
            user_dict.pop('position_id', None)
            user_dict.pop('department_id', None)
            user_list.append(user_dict)
        return user_list
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка пользователей")


async def get_user(db: AsyncSession, user_id: int):
    try:
        result = await db.execute(
            select(User)
            .options(
                selectinload(User.organization),
                selectinload(User.position),
                selectinload(User.department),
                selectinload(User.img)
            )
            .filter(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("Пользователь не найден")
        user_dict = user.__dict__.copy()
        user_dict['photo_url'] = user.img.path if user.img else None
        user_dict['organization'] = user.organization.name if user.organization else None
        user_dict['position'] = user.position.name if user.position else None
        user_dict['department'] = user.department.name if user.department else None
        user_dict['phone_number'] = user.phone_number
        user_dict.pop('img', None)
        user_dict.pop('img_id', None)
        user_dict.pop('organization_id', None)
        user_dict.pop('position_id', None)
        user_dict.pop('department_id', None)
        return user_dict
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


def _generate_temporary_password(length: int = 12) -> str:
    """
    Генерация временного пароля
    
    Args:
        length: Длина пароля (по умолчанию 12 символов)
    
    Returns:
        Сгенерированный пароль
    """
    # Используем буквы, цифры и специальные символы
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    # Генерируем пароль, исключая похожие символы
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


async def reset_user_password(db: AsyncSession, email: str) -> dict:
    """
    Восстановление пароля пользователя
    
    Args:
        db: Сессия базы данных
        email: Email пользователя
    
    Returns:
        Словарь с результатом операции
    """
    try:
        # Находим пользователя по email
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundException(f"Пользователь с email {email} не найден")
        
        # Проверяем, что пользователь не является гостем
        if user.role and user.role.code == "guest":
            raise DatabaseException("Восстановление пароля недоступно для гостевых пользователей")
        
        # Генерируем новый временный пароль
        new_password = _generate_temporary_password()
        
        # Хешируем новый пароль
        hashed_password = get_password_hash(new_password)
        
        # Обновляем пароль в базе данных
        user.password = hashed_password
        await db.commit()
        await db.refresh(user)
        
        # Отправляем email с новым паролем
        try:
            await email_service.send_password_reset_email(email, new_password, user.name)
        except Exception as email_error:
            # Если не удалось отправить email, откатываем изменения пароля
            await db.rollback()
            raise DatabaseException(f"Не удалось отправить email: {str(email_error)}")
        
        return {
            "message": f"Новый пароль отправлен на email {email}",
            "success": True,
            "user_id": user.id,
            "user_name": user.name
        }
        
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при восстановлении пароля: {str(e)}")
    except (NotFoundException, DatabaseException):
        # Перебрасываем исключения, которые мы создали
        raise
    except Exception as e:
        await db.rollback()
        raise DatabaseException(f"Неожиданная ошибка при восстановлении пароля: {str(e)}")


async def get_user_by_email(db: AsyncSession, email: str) -> User:
    """
    Получение пользователя по email
    
    Args:
        db: Сессия базы данных
        email: Email пользователя
    
    Returns:
        Пользователь или None
    """
    try:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении пользователя по email")


async def get_organizations(db: AsyncSession):
    try:
        result = await db.execute(select(Organization))
        return result.scalars().all()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка организаций")

async def get_positions(db: AsyncSession):
    try:
        result = await db.execute(select(Position))
        return result.scalars().all()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка позиций")

async def get_departments(db: AsyncSession):
    try:
        result = await db.execute(select(Department))
        return result.scalars().all()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка департаментов")
