from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.crud import (
    create_faq,
    get_faq,
    get_faqs,
    answer_faq,
    increment_faq_hits,
    admin_moderator_required,
    authorized_required,
    get_current_user,
    get_faq_category,
    is_user_in_group,
)
from app.dependencies import get_db
from app.schemas import FaqCreate, FaqAnswerUpdate, FaqInDB
from app.exceptions import DatabaseException
from app.models import User

router = APIRouter(prefix="/api/faq", tags=["FAQ"])


@router.post("/", response_model=FaqInDB)
async def create_faq_route(
    data: FaqCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        category = await get_faq_category(db, data.category_id)
        if (
            category.user_group_id is not None
            and user.role.code not in ["admin", "moderator"]
            and not await is_user_in_group(db, category.user_group_id, user.id)
        ):
            raise HTTPException(status_code=403, detail="Нет доступа к категории")
        return await create_faq(db, data, user.id, user.name)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании вопроса FAQ")


@router.get("/", response_model=list[FaqInDB])
async def list_faq_route(
    category_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(authorized_required),
):
    try:
        if category_id is not None:
            category = await get_faq_category(db, category_id)
            if (
                category.user_group_id is not None
                and user.role.code not in ["admin", "moderator"]
                and not await is_user_in_group(db, category.user_group_id, user.id)
            ):
                raise HTTPException(status_code=403, detail="Нет доступа к категории")
        faqs = await get_faqs(db, category_id)
        if user.role.code not in ["admin", "moderator"]:
            filtered = []
            for f in faqs:
                cat = await get_faq_category(db, f.category_id)
                if cat.user_group_id is None or await is_user_in_group(db, cat.user_group_id, user.id):
                    filtered.append(f)
            faqs = filtered
        return faqs
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении вопросов FAQ")


@router.get("/{faq_id}/", response_model=FaqInDB)
async def get_faq_route(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(authorized_required),
):
    try:
        faq = await get_faq(db, faq_id)
        category = await get_faq_category(db, faq.category_id)
        if (
            category.user_group_id is not None
            and user.role.code not in ["admin", "moderator"]
            and not await is_user_in_group(db, category.user_group_id, user.id)
        ):
            raise HTTPException(status_code=403, detail="Нет доступа к вопросу")
        await increment_faq_hits(db, faq_id)
        return faq
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении вопроса FAQ")


@router.put("/{faq_id}/answer/", response_model=FaqInDB)
async def answer_faq_route(
    faq_id: int,
    data: FaqAnswerUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_moderator_required),
):
    try:
        return await answer_faq(db, faq_id, data)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении вопроса FAQ")

