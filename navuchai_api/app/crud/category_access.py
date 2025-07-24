from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.models import CategoryAccess
from app.exceptions import NotFoundException


async def grant_category_access(db: AsyncSession, category_id: int, user_id: int):
    existing = await db.execute(
        select(CategoryAccess).where(
            and_(CategoryAccess.category_id == category_id, CategoryAccess.user_id == user_id)
        )
    )
    if existing.scalar_one_or_none():
        return
    access = CategoryAccess(category_id=category_id, user_id=user_id)
    db.add(access)
    await db.commit()


async def revoke_category_access(db: AsyncSession, category_id: int, user_id: int):
    result = await db.execute(
        select(CategoryAccess).where(
            and_(CategoryAccess.category_id == category_id, CategoryAccess.user_id == user_id)
        )
    )
    access = result.scalar_one_or_none()
    if not access:
        raise NotFoundException("Запись не найдена")
    await db.delete(access)
    await db.commit()


async def get_user_categories(db: AsyncSession, user_id: int):
    result = await db.execute(select(CategoryAccess).where(CategoryAccess.user_id == user_id))
    return result.scalars().all()


async def user_has_category_access(db: AsyncSession, category_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(CategoryAccess).where(
            and_(CategoryAccess.category_id == category_id, CategoryAccess.user_id == user_id)
        )
    )
    return result.scalar_one_or_none() is not None
