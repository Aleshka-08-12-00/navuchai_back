from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models import Question, TestQuestion
from app.schemas.question import QuestionCreate, QuestionUpdate
from app.exceptions import NotFoundException, DatabaseException


# Получение списка вопросов
async def get_questions(db: AsyncSession):
    try:
        result = await db.execute(select(Question))
        return result.scalars().all()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка вопросов")


# Получение конкретного вопроса
async def get_question(db: AsyncSession, question_id: int):
    try:
        result = await db.execute(select(Question).filter(Question.id == question_id))
        question = result.scalar_one_or_none()
        if not question:
            raise NotFoundException("Вопрос не найден")
        return question
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении вопроса")


async def get_questions_by_test_id(db: AsyncSession, test_id: int):
    try:
        result = await db.execute(
            select(TestQuestion, Question)
            .join(Question, TestQuestion.question_id == Question.id)
            .options(selectinload(Question.test_questions))
            .where(TestQuestion.test_id == test_id)
        )
        test_question_pairs = result.all()

        return [
            {
                "question": tq.Question,
                "position": tq.TestQuestion.position,
                "required": tq.TestQuestion.required,
                "max_score": tq.TestQuestion.max_score,
            }
            for tq in test_question_pairs
        ]
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при получении вопросов теста: {str(e)}")
        raise DatabaseException("Ошибка при получении вопросов теста")


# Создание нового вопроса
async def create_question(db: AsyncSession, question: QuestionCreate):
    new_question = Question(
        text=question.text,
        text_abstract=question.text_abstract,
        type=question.type,
        reviewable=question.reviewable,
        answers=question.answers
    )
    db.add(new_question)
    try:
        await db.commit()
        await db.refresh(new_question)
        return new_question
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при создании вопроса")


# Обновление вопроса
async def update_question(db: AsyncSession, question_id: int, question: QuestionUpdate):
    existing_question = await get_question(db, question_id)
    if not existing_question:
        raise NotFoundException("Вопрос не найден")

    existing_question.text = question.text
    existing_question.text_abstract = question.text_abstract
    existing_question.type = question.type
    existing_question.reviewable = question.reviewable
    existing_question.answers = question.answers

    try:
        await db.commit()
        await db.refresh(existing_question)
        return existing_question
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при обновлении вопроса")


# Удаление вопроса
async def delete_question(db: AsyncSession, question_id: int):
    existing_question = await get_question(db, question_id)
    if not existing_question:
        raise NotFoundException("Вопрос не найден")

    await db.delete(existing_question)
    try:
        await db.commit()
        return existing_question
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при удалении вопроса")
