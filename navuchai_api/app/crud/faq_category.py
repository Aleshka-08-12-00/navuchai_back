from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models import FaqCategory
from app.schemas.faq_category import FaqCategoryCreate, FaqCategoryUpdate
from app.exceptions import DatabaseException, NotFoundException


async def create_faq_category(db: AsyncSession, data: FaqCategoryCreate) -> FaqCategory:
    try:
        obj = FaqCategory(**data.model_dump())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании категории FAQ: {str(e)}")


async def get_faq_category(db: AsyncSession, category_id: int) -> FaqCategory:
    try:
        result = await db.execute(select(FaqCategory).where(FaqCategory.id == category_id))
        obj = result.scalar_one_or_none()
        if not obj:
            raise NotFoundException("Категория FAQ не найдена")
        return obj
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении категории FAQ: {str(e)}")


async def get_faq_categories(db: AsyncSession) -> list[FaqCategory]:
    try:
        result = await db.execute(select(FaqCategory))
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении категорий FAQ: {str(e)}")


async def update_faq_category(db: AsyncSession, category_id: int, data: FaqCategoryUpdate) -> FaqCategory:
    try:
        obj = await get_faq_category(db, category_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        await db.commit()
        await db.refresh(obj)
        return obj
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении категории FAQ: {str(e)}")


async def delete_faq_category(db: AsyncSession, category_id: int) -> None:
    try:
        obj = await get_faq_category(db, category_id)
        await db.delete(obj)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении категории FAQ: {str(e)}")
