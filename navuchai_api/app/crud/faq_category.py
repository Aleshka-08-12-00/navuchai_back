from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.models import FaqCategory, FaqCategoryAccess
from app.schemas.faq_category import FaqCategoryCreate, FaqCategoryUpdate
from app.exceptions import DatabaseException, NotFoundException


async def create_faq_category(db: AsyncSession, data: FaqCategoryCreate) -> FaqCategory:
    try:
        obj = FaqCategory(**data.model_dump(exclude={"user_group_ids"}))
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        if data.user_group_ids:
            new_accesses = [FaqCategoryAccess(user_group_id=g, faq_category_id=obj.id) for g in data.user_group_ids]
            db.add_all(new_accesses)
            await db.commit()
            # Перезагружаем объект с связями
            return await get_faq_category(db, obj.id)
        return obj
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании категории FAQ: {str(e)}")


async def get_faq_category(db: AsyncSession, category_id: int) -> FaqCategory:
    try:
        # Очищаем сессию перед запросом, чтобы избежать кэширования
        await db.flush()
        result = await db.execute(
            select(FaqCategory).options(selectinload(FaqCategory.accesses)).where(FaqCategory.id == category_id)
        )
        obj = result.scalar_one_or_none()
        if not obj:
            raise NotFoundException("Категория FAQ не найдена")
        return obj
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении категории FAQ: {str(e)}")


async def get_faq_categories(db: AsyncSession) -> list[FaqCategory]:
    try:
        result = await db.execute(select(FaqCategory).options(selectinload(FaqCategory.accesses)))
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении категорий FAQ: {str(e)}")


async def update_faq_category(db: AsyncSession, category_id: int, data: FaqCategoryUpdate) -> FaqCategory:
    try:
        obj = await get_faq_category(db, category_id)
        data_dict = data.model_dump(exclude_unset=True, exclude={"user_group_id"})
        for field, value in data_dict.items():
            setattr(obj, field, value)
        
        # Обрабатываем user_group_ids только если они явно переданы в запросе
        # Проверяем, было ли поле user_group_ids в исходных данных
        # Поле было передано, только если клиент явно прислал его в теле запроса
        if 'user_group_id' in getattr(data, 'model_fields_set', set()):
            # Если передан один ID: добавляем его, если ещё нет; если None — очищаем все
            if data.user_group_id is not None:
                existing_group_ids = {a.user_group_id for a in obj.accesses}
                if data.user_group_id not in existing_group_ids:
                    new_access = FaqCategoryAccess(user_group_id=data.user_group_id, faq_category_id=category_id)
                    db.add(new_access)
                    # Добавляем новую запись в связь объекта
                    obj.accesses.append(new_access)
            else:
                for access in obj.accesses:
                    await db.delete(access)
                obj.accesses.clear()
        
        await db.commit()
        # Принудительно перезагружаем объект с актуальными связями
        await db.refresh(obj, attribute_names=['accesses'])
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
