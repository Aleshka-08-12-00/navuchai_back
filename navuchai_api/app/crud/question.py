from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Question
from app.schemas.question import QuestionCreate, QuestionUpdate


# Получение списка вопросов
async def get_questions(db: AsyncSession):
    result = await db.execute(select(Question))
    return result.scalars().all()


# Получение конкретного вопроса
async def get_question(db: AsyncSession, question_id: int):
    result = await db.execute(select(Question).filter(Question.id == question_id))
    return result.scalar_one_or_none()


# Создание нового вопроса
async def create_question(db: AsyncSession, question: QuestionCreate):
    new_question = Question(
        text=question.text,
        type=question.type,
        options=question.options
    )
    db.add(new_question)
    try:
        await db.commit()
        await db.refresh(new_question)
        return new_question
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Обновление вопроса
async def update_question(db: AsyncSession, question_id: int, question: QuestionUpdate):
    existing_question = await get_question(db, question_id)
    if not existing_question:
        return None

    existing_question.text = question.text
    existing_question.type = question.type
    existing_question.options = question.options

    try:
        await db.commit()
        await db.refresh(existing_question)
        return existing_question
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Удаление вопроса
async def delete_question(db: AsyncSession, question_id: int):
    existing_question = await get_question(db, question_id)
    if not existing_question:
        return None

    await db.delete(existing_question)
    try:
        await db.commit()
        return existing_question
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
