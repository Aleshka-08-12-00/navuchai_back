from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.crud import (
    create_faq_category,
    get_faq_category,
    get_faq_categories,
    update_faq_category,
    delete_faq_category,
    admin_moderator_required,
    authorized_required,
)
from app.dependencies import get_db
from app.schemas import (
    FaqCategoryCreate,
    FaqCategoryUpdate,
    FaqCategoryInDB,
)
from app.exceptions import DatabaseException
from app.models import User

router = APIRouter(prefix="/api/faq-categories", tags=["FAQ Categories"])


@router.post("/", response_model=FaqCategoryInDB)
async def create_category_route(
    data: FaqCategoryCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_moderator_required),
):
    try:
        return await create_faq_category(db, data)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании категории FAQ")


@router.get("/", response_model=list[FaqCategoryInDB])
async def list_categories_route(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(authorized_required),
):
    try:
        return await get_faq_categories(db)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении категорий FAQ")


@router.get("/{category_id}/", response_model=FaqCategoryInDB)
async def get_category_route(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(authorized_required),
):
    try:
        return await get_faq_category(db, category_id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении категории FAQ")


@router.put("/{category_id}/", response_model=FaqCategoryInDB)
async def update_category_route(
    category_id: int,
    data: FaqCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_moderator_required),
):
    try:
        return await update_faq_category(db, category_id, data)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении категории FAQ")


@router.delete("/{category_id}/")
async def delete_category_route(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_moderator_required),
):
    try:
        await delete_faq_category(db, category_id)
        return {"detail": "Категория FAQ удалена"}
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при удалении категории FAQ")
