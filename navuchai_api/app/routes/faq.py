from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.crud import (
    create_faq,
    get_faq,
    get_faqs,
    answer_faq,
    increment_faq_hits,
    get_new_answers_count,
    get_new_answers_counts,
    admin_moderator_required,
    authorized_required,
    get_current_user,
    get_faq_category,
    is_user_in_group,
)
from app.dependencies import get_db
from app.schemas import FaqCreate, FaqAnswerUpdate, FaqInDB, NewAnswersCount
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
        if category.user_group_ids and user.role.code not in ["admin", "moderator"]:
            has_access = False
            for gid in category.user_group_ids:
                if await is_user_in_group(db, gid, user.id):
                    has_access = True
                    break
            if not has_access:
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
            if category.user_group_ids and user.role.code not in ["admin", "moderator"]:
                has_access = False
                for gid in category.user_group_ids:
                    if await is_user_in_group(db, gid, user.id):
                        has_access = True
                        break
                if not has_access:
                    raise HTTPException(status_code=403, detail="Нет доступа к категории")
        faqs = await get_faqs(db, category_id)
        if user.role.code not in ["admin", "moderator"]:
            filtered = []
            for f in faqs:
                cat = await get_faq_category(db, f.category_id)
                if not cat.user_group_ids:
                    filtered.append(f)
                else:
                    for gid in cat.user_group_ids:
                        if await is_user_in_group(db, gid, user.id):
                            filtered.append(f)
                            break
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
        if category.user_group_ids and user.role.code not in ["admin", "moderator"]:
            has_access = False
            for gid in category.user_group_ids:
                if await is_user_in_group(db, gid, user.id):
                    has_access = True
                    break
            if not has_access:
                raise HTTPException(status_code=403, detail="Нет доступа к вопросу")
        await increment_faq_hits(db, faq_id)
        if faq.owner_id == user.id and faq.has_new_answer:
            faq.has_new_answer = False
            await db.commit()
            await db.refresh(faq)
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
        return await answer_faq(db, faq_id, data, user.id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении вопроса FAQ")


@router.get("/new-answers/count/", response_model=int)
async def new_answers_count_route(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return await get_new_answers_count(db, user.id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении количества новых ответов")


@router.get("/new-answers/count/all/", response_model=list[NewAnswersCount])
async def new_answers_count_all_route(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_moderator_required),
):
    try:
        return await get_new_answers_counts(db)
    except SQLAlchemyError:
        raise DatabaseException(
            "Ошибка при получении количества новых ответов для пользователей"
        )

