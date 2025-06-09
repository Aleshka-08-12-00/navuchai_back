from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from app.models import Result, UserAnswer, Test, Question, User
from app.schemas.result import ResultCreate
from app.exceptions import NotFoundException, DatabaseException
from app.utils.answer_checker import process_test_results
from app.crud.question import get_questions_by_test_id
import logging

logger = logging.getLogger(__name__)

async def create_result(db: AsyncSession, result_data: ResultCreate):
    try:
        # Проверяем существование теста
        test_result = await db.execute(
            select(Test).where(Test.id == result_data.test_id)
        )
        test = test_result.scalar_one_or_none()
        if not test:
            raise NotFoundException(f"Тест с ID {result_data.test_id} не найден")

        # Проверяем существование пользователя
        user_result = await db.execute(
            select(User).where(User.id == result_data.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundException(f"Пользователь с ID {result_data.user_id} не найден")

        # Получаем все вопросы теста с их параметрами
        questions = await get_questions_by_test_id(db, result_data.test_id)
        
        # Обрабатываем ответы и получаем результаты
        test_results = process_test_results(questions, result_data.answers, test.time_limit)
        
        # Преобразуем datetime в строки
        for answer in test_results['checked_answers']:
            if isinstance(answer.get('time_start'), datetime):
                answer['time_start'] = answer['time_start'].isoformat()
            if isinstance(answer.get('time_end'), datetime):
                answer['time_end'] = answer['time_end'].isoformat()
        
        # Добавляем информацию о времени в результаты
        test_results['time_start'] = result_data.time_start.isoformat()
        test_results['time_end'] = result_data.time_end.isoformat()
        test_results['total_time_seconds'] = int((result_data.time_end - result_data.time_start).total_seconds())
        
        # Создаем результат
        new_result = Result(
            test_id=result_data.test_id,
            user_id=result_data.user_id,
            score=test_results['total_score'],
            result=test_results
        )
        db.add(new_result)
        await db.flush()

        # Создаем ответы пользователя
        for answer in result_data.answers:
            # Проверяем существование вопроса
            question_result = await db.execute(
                select(Question).where(Question.id == answer.question_id)
            )
            question = question_result.scalar_one_or_none()
            if not question:
                raise NotFoundException(f"Вопрос с ID {answer.question_id} не найден")

            # Добавляем время в JSON ответа
            answer_data = answer.answer.copy()
            answer_data['time_start'] = answer.time_start.isoformat()
            answer_data['time_end'] = answer.time_end.isoformat()

            new_answer = UserAnswer(
                result_id=new_result.id,
                question_id=answer.question_id,
                user_id=result_data.user_id,
                answer=answer_data
            )
            db.add(new_answer)

        await db.commit()
        await db.refresh(new_result)

        return new_result

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Ошибка при создании результата: {str(e)}")
        raise DatabaseException(f"Ошибка при сохранении результата: {str(e)}")


async def get_result(db: AsyncSession, result_id: int):
    try:
        # Получаем результат с ответами
        stmt = (
            select(Result)
            .options(selectinload(Result.user_answers))
            .where(Result.id == result_id)
        )
        result = await db.execute(stmt)
        result_obj = result.scalar_one_or_none()

        if not result_obj:
            raise NotFoundException(f"Результат с ID {result_id} не найден")

        return result_obj
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при получении результата: {str(e)}")


async def get_user_results(db: AsyncSession, user_id: int) -> List[Result]:
    try:
        result = await db.execute(
            select(Result)
            .where(Result.user_id == user_id)
            .order_by(Result.created_at.desc())
        )
        return result.scalars().all()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении результатов пользователя")


async def get_test_results(db: AsyncSession, test_id: int):
    try:
        # Получаем результаты с ответами
        stmt = (
            select(Result)
            .options(selectinload(Result.user_answers))
            .where(Result.test_id == test_id)
        )
        result = await db.execute(stmt)
        results = result.scalars().all()

        return results
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при получении результатов теста: {str(e)}")


async def get_all_results(db: AsyncSession) -> List[Result]:
    try:
        # Получаем результаты с ответами
        stmt = (
            select(Result)
            .options(selectinload(Result.user_answers))
            .order_by(Result.created_at.desc())
        )
        result = await db.execute(stmt)
        results = result.scalars().all()

        return results
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при получении списка результатов: {str(e)}")
