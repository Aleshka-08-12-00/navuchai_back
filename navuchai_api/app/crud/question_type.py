from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.models import QuestionType
from app.schemas.question_type import QuestionTypeCreate, QuestionTypeUpdate
from app.exceptions import NotFoundException, DatabaseException


async def get_question_types(db: AsyncSession):
    try:
        result = await db.execute(select(QuestionType))
        return result.scalars().all()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка типов вопросов")


async def get_question_type(db: AsyncSession, type_id: int):
    try:
        result = await db.execute(select(QuestionType).filter(QuestionType.id == type_id))
        question_type = result.scalar_one_or_none()
        if not question_type:
            raise NotFoundException("Тип вопроса не найден")
        return question_type
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении типа вопроса")


async def create_question_type(db: AsyncSession, question_type: QuestionTypeCreate):
    try:
        db_question_type = QuestionType(**question_type.model_dump())
        db.add(db_question_type)
        await db.commit()
        await db.refresh(db_question_type)
        return db_question_type
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при создании типа вопроса")


async def update_question_type(db: AsyncSession, type_id: int, question_type: QuestionTypeUpdate):
    try:
        db_question_type = await get_question_type(db, type_id)
        for key, value in question_type.model_dump().items():
            setattr(db_question_type, key, value)
        await db.commit()
        await db.refresh(db_question_type)
        return db_question_type
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при обновлении типа вопроса")


async def delete_question_type(db: AsyncSession, type_id: int):
    try:
        db_question_type = await get_question_type(db, type_id)
        await db.delete(db_question_type)
        await db.commit()
        return db_question_type
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при удалении типа вопроса") 