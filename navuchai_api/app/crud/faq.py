from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update as sql_update
from sqlalchemy.orm import selectinload

from datetime import datetime
from sqlalchemy import func
from app.models import Faq
from app.schemas.faq import FaqCreate, FaqAnswerUpdate
from app.exceptions import DatabaseException, NotFoundException


async def create_faq(db: AsyncSession, data: FaqCreate, owner_id: int, username: str) -> Faq:
    try:
        obj = Faq(
            category_id=data.category_id,
            question=data.question,
            owner_id=owner_id,
            username=username,
            question_file_url=data.question_file_url,
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании вопроса FAQ: {str(e)}")


async def get_faq(db: AsyncSession, faq_id: int) -> Faq:
    try:
        res = await db.execute(
            select(Faq)
            .options(selectinload(Faq.answer_author))
            .where(Faq.id == faq_id)
        )
        obj = res.scalar_one_or_none()
        if not obj:
            raise NotFoundException("Вопрос FAQ не найден")
        return obj
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении вопроса FAQ: {str(e)}")


async def get_faqs(db: AsyncSession, category_id: int | None = None) -> list[Faq]:
    try:
        stmt = select(Faq).options(selectinload(Faq.answer_author))
        if category_id is not None:
            stmt = stmt.where(Faq.category_id == category_id)
        result = await db.execute(stmt)
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении вопросов FAQ: {str(e)}")


async def answer_faq(db: AsyncSession, faq_id: int, data: FaqAnswerUpdate, author_id: int) -> Faq:
    obj = await get_faq(db, faq_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    obj.answered_at = datetime.utcnow()
    obj.answer_author_id = author_id
    obj.has_new_answer = True
    try:
        await db.commit()
        await db.refresh(obj)
        return obj
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении вопроса FAQ: {str(e)}")


async def increment_faq_hits(db: AsyncSession, faq_id: int) -> None:
    try:
        await db.execute(sql_update(Faq).where(Faq.id == faq_id).values(hits=Faq.hits + 1))
        await db.commit()
    except SQLAlchemyError:
        await db.rollback()


async def get_new_answers_count(db: AsyncSession, user_id: int) -> int:
    try:
        res = await db.execute(
            select(func.count()).select_from(Faq).where(
                Faq.owner_id == user_id, Faq.has_new_answer == True
            )
        )
        return res.scalar_one()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении количества новых ответов: {str(e)}")

