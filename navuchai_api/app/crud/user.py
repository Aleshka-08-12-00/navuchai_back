from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from app.models import User, Role
from app.schemas.user import UserUpdate
from app.utils import format_user


async def get_users(db: AsyncSession):
    result = await db.execute(
        select(User, Role.name).join(Role, User.role_id == Role.id)
    )
    rows = result.all()

    return [format_user(user, role_name)for user, role_name in rows]


async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(User, Role.name)
        .join(Role, User.role_id == Role.id)
        .where(User.id == user_id)
    )
    row = result.one_or_none()

    if not row:
        return None
    return format_user(*row)


async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user_id: int, user: UserUpdate):
    existing_user = await get_user_by_id(db, user_id)
    if not existing_user:
        return None

    update_data = user.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing_user, key, value)

    try:
        await db.commit()
        await db.refresh(existing_user)
        return existing_user
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


async def delete_user(db: AsyncSession, user_id: int):
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    await db.delete(user)
    try:
        await db.commit()
        return user
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
