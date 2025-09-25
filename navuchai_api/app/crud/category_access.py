from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models import CategoryAccess
from app.schemas.category_access import CategoryAccessCreate, CategoryAccessUpdate
from app.exceptions import DatabaseException, NotFoundException
from datetime import timezone


def _to_aware_utc(dt):
    if dt is None:
        return None
    # Приводим к UTC и оставляем tzinfo (TIMESTAMPTZ)
    if getattr(dt, 'tzinfo', None) is not None:
        return dt.astimezone(timezone.utc)
    # Наивную дату считаем UTC
    return dt.replace(tzinfo=timezone.utc)


async def create_category_access(db: AsyncSession, payload: CategoryAccessCreate) -> CategoryAccess:
    try:
        # ensure unique pair (category_id, user_group_id)
        existing = await db.execute(
            select(CategoryAccess).where(
                CategoryAccess.category_id == payload.category_id,
                CategoryAccess.user_group_id == payload.user_group_id,
            )
        )
        if existing.scalar_one_or_none():
            raise DatabaseException("Доступ уже существует для этой группы и категории")

        data = payload.dict(exclude_unset=True)
        data['start_date'] = _to_aware_utc(data.get('start_date'))
        data['end_date'] = _to_aware_utc(data.get('end_date'))

        entity = CategoryAccess(**data)
        db.add(entity)
        await db.commit()
        await db.refresh(entity)
        return entity
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании доступа категории: {str(e)}")


async def get_category_access(db: AsyncSession, access_id: int) -> CategoryAccess:
    try:
        result = await db.execute(select(CategoryAccess).where(CategoryAccess.id == access_id))
        entity = result.scalar_one_or_none()
        if not entity:
            raise NotFoundException("Доступ к категории не найден")
        return entity
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении доступа категории: {str(e)}")


async def list_category_accesses(db: AsyncSession, category_id: int | None = None, user_group_id: int | None = None) -> list[CategoryAccess]:
    try:
        stmt = select(CategoryAccess)
        if category_id is not None:
            stmt = stmt.where(CategoryAccess.category_id == category_id)
        if user_group_id is not None:
            stmt = stmt.where(CategoryAccess.user_group_id == user_group_id)
        result = await db.execute(stmt.order_by(CategoryAccess.id))
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении списка доступов категорий: {str(e)}")


async def update_category_access(db: AsyncSession, access_id: int, payload: CategoryAccessUpdate) -> CategoryAccess:
    try:
        entity = await get_category_access(db, access_id)
        data = payload.dict(exclude_unset=True)
        if 'start_date' in data:
            data['start_date'] = _to_aware_utc(data['start_date'])
        if 'end_date' in data:
            data['end_date'] = _to_aware_utc(data['end_date'])

        for field, value in data.items():
            setattr(entity, field, value)
        await db.commit()
        await db.refresh(entity)
        return entity
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении доступа категории: {str(e)}")


async def delete_category_access(db: AsyncSession, access_id: int) -> None:
    try:
        entity = await get_category_access(db, access_id)
        await db.delete(entity)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении доступа категории: {str(e)}")


