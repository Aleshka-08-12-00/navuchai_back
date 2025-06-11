from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud import get_question, get_test
from app.models import TestQuestion
from app.exceptions import NotFoundException, DatabaseException


# Создание связи между тестом и вопросом (test_question)
async def create_test_question(db: AsyncSession, test_id: int, question_id: int) -> TestQuestion:
    """
    Создает связь между тестом и вопросом с фиксированными значениями:
    - position = 1
    - required = True
    - max_score = 1
    """
    test_question = TestQuestion(
        test_id=test_id,
        question_id=question_id,
        position=1,
        required=True,
        max_score=1
    )
    db.add(test_question)
    await db.commit()
    await db.refresh(test_question)
    return test_question


# Удаление связи между тестом и вопросом
async def delete_test_question(db: AsyncSession, test_id: int, question_id: int) -> bool:
    """
    Удаляет связь между тестом и вопросом
    """
    result = await db.execute(
        select(TestQuestion).where(
            TestQuestion.test_id == test_id,
            TestQuestion.question_id == question_id
        )
    )
    test_question = result.scalar_one_or_none()
    if not test_question:
        raise NotFoundException("Test-Question relation not found")
    await db.delete(test_question)
    await db.commit()
    return True
