from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Question, TestQuestion
from app.schemas.question import QuestionCreate, QuestionUpdate


# Получение списка вопросов
async def get_questions(db: AsyncSession):
    result = await db.execute(select(Question))
    return result.scalars().all()


# Получение конкретного вопроса
async def get_question(db: AsyncSession, question_id: int):
    result = await db.execute(select(Question).filter(Question.id == question_id))
    return result.scalar_one_or_none()


async def get_questions_by_test_id(db: AsyncSession, test_id: int):
    result = await db.execute(
        select(TestQuestion, Question)
        .join(Question, TestQuestion.question_id == Question.id)
        .where(TestQuestion.test_id == test_id)
    )
    test_question_pairs = result.all()

    # Собираем данные в нужной форме
    return [
        {
            "question": tq.Question,
            "position": tq.TestQuestion.position,
            "required": tq.TestQuestion.required,
            "max_score": tq.TestQuestion.max_score,
        }
        for tq in test_question_pairs
    ]


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
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Обновление вопроса
async def update_question(db: AsyncSession, question_id: int, question: QuestionUpdate):
    existing_question = await get_question(db, question_id)
    if not existing_question:
        return None

    existing_question.text = question.text
    existing_question.text_abstract = question.text_abstract
    existing_question.type = question.type
    existing_question.reviewable = question.reviewable
    existing_question.answers = question.answers

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
