from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.exceptions import DatabaseException, NotFoundException

async def create_category(db: AsyncSession, category: CategoryCreate) -> Category:
    try:
        db_category = Category(name=category.name)
        db.add(db_category)
        await db.commit()
        await db.refresh(db_category)
        return db_category
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании категории: {str(e)}")

async def get_category(db: AsyncSession, category_id: int) -> Category:
    try:
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if not category:
            raise NotFoundException("Категория не найдена")
        return category
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении категории: {str(e)}")

async def get_categories(db: AsyncSession) -> list[Category]:
    try:
        result = await db.execute(select(Category))
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении списка категорий: {str(e)}")

async def update_category(db: AsyncSession, category_id: int, category: CategoryUpdate) -> Category:
    try:
        db_category = await get_category(db, category_id)
        for field, value in category.dict(exclude_unset=True).items():
            setattr(db_category, field, value)
        await db.commit()
        await db.refresh(db_category)
        return db_category
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении категории: {str(e)}")

async def delete_category(db: AsyncSession, category_id: int) -> None:
    try:
        db_category = await get_category(db, category_id)
        await db.delete(db_category)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении категории: {str(e)}") 