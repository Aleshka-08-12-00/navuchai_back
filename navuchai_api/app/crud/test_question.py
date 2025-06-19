from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud import get_question, get_test
from app.models import TestQuestion, Question
from app.exceptions import NotFoundException, DatabaseException


# Создание связи между тестом и вопросом (test_question)
async def create_test_question(db: AsyncSession, test_id: int, question_id: int) -> TestQuestion:
    """
    Создает связь между тестом и вопросом.
    max_score берется из answers.settings.correctScore вопроса.
    """
    # Получаем вопрос для извлечения correctScore
    question_result = await db.execute(
        select(Question).where(Question.id == question_id)
    )
    question = question_result.scalar_one_or_none()
    if not question:
        raise NotFoundException(f"Вопрос с ID {question_id} не найден")
    
    # Извлекаем correctScore из настроек вопроса
    answers = question.answers
    correct_score = 1  # значение по умолчанию
    if isinstance(answers, dict) and 'settings' in answers:
        settings = answers.get('settings', {})
        correct_score = settings.get('correctScore', 1)
    
    test_question = TestQuestion(
        test_id=test_id,
        question_id=question_id,
        position=1,
        required=True,
        max_score=correct_score
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
