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
        result = await db.execute(
            select(Question)
            .options(selectinload(Question.type))
        )
        return result.scalars().all()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка вопросов")


# Получение конкретного вопроса
async def get_question(db: AsyncSession, question_id: int):
    try:
        result = await db.execute(
            select(Question)
            .options(selectinload(Question.type))
            .filter(Question.id == question_id)
        )
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
            .options(selectinload(Question.type))
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
        type_id=question.type_id,
        reviewable=question.reviewable,
        answers=question.answers,
        time_limit=question.time_limit
    )
    db.add(new_question)
    try:
        await db.commit()
        await db.refresh(new_question)
        # Загружаем связанные данные
        result = await db.execute(
            select(Question)
            .options(selectinload(Question.type))
            .where(Question.id == new_question.id)
        )
        return result.scalar_one()
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при создании вопроса")


# Обновление вопроса
async def update_question(db: AsyncSession, question_id: int, question: QuestionUpdate):
    existing_question = await get_question(db, question_id)
    if not existing_question:
        raise NotFoundException("Вопрос не найден")

    update_data = question.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing_question, key, value)

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
