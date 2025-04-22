from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud import get_question, get_test
from app.models import TestQuestion
from app.exceptions import NotFoundException, DatabaseException


# Создание связи между тестом и вопросом (test_question)
async def create_test_question(db: AsyncSession, test_id: int, question_id: int, position: int, required: bool, max_score: int):
    try:
        # Проверяем, существует ли тест и вопрос
        test = await get_test(db, test_id)
        question = await get_question(db, question_id)

        if not test:
            raise NotFoundException("Тест не найден")
        if not question:
            raise NotFoundException("Вопрос не найден")

        new_test_question = TestQuestion(test_id=test_id, question_id=question_id, position=position, required=position, max_score=position)
        db.add(new_test_question)
        await db.commit()
        await db.refresh(new_test_question)
        return new_test_question
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при создании связи теста и вопроса")


# Удаление связи между тестом и вопросом
async def delete_test_question(db: AsyncSession, test_id: int, question_id: int):
    try:
        async with db.begin():
            test_question = await db.execute(
                select(TestQuestion).filter(
                    TestQuestion.test_id == test_id,
                    TestQuestion.question_id == question_id
                )
            )
            test_question = test_question.scalar_one_or_none()

            if not test_question:
                raise NotFoundException("Связь теста и вопроса не найдена")

            await db.delete(test_question)
            await db.commit()
            return test_question
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при удалении связи теста и вопроса")
