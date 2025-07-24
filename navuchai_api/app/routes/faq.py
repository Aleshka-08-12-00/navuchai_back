from fastapi import APIRouter, Depends
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
        return await get_faqs(db, category_id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении вопросов FAQ")


@router.get("/{faq_id}/", response_model=FaqInDB)
async def get_faq_route(
    faq_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(authorized_required),
):
    try:
        await increment_faq_hits(db, faq_id)
        return await get_faq(db, faq_id)
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

