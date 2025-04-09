from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud import get_question, get_test
from app.models import TestQuestion


# Создание связи между тестом и вопросом (test_question)
async def create_test_question(db: AsyncSession, test_id: int, question_id: int, position: int, required: bool, max_score: int):
    # Проверяем, существует ли тест и вопрос
    test = await get_test(db, test_id)
    question = await get_question(db, question_id)

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Создаём запись в таблице test_question для связи
    new_test_question = TestQuestion(test_id=test_id, question_id=question_id, position=position, required=position, max_score=position)
    db.add(new_test_question)
    try:
        await db.commit()
        await db.refresh(new_test_question)
        return new_test_question
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Удаление связи между тестом и вопросом
async def delete_test_question(db: AsyncSession, test_id: int, question_id: int):
    async with db.begin():
        # Находим связь между тестом и вопросом
        test_question = await db.execute(
            select(TestQuestion).filter(
                TestQuestion.test_id == test_id,
                TestQuestion.question_id == question_id
            )
        )
        test_question = test_question.scalar_one_or_none()

        if not test_question:
            return None  # Связь не найдена

        # Удаляем найденную связь
        await db.delete(test_question)

        try:
            await db.commit()
            return test_question  # Возвращаем удалённую связь
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
