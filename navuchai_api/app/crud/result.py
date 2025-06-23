from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlalchemy import text
from typing import List
from datetime import datetime

from app.models import Result, UserAnswer, Test, Question, User
from app.schemas.result import ResultCreate
from app.exceptions import NotFoundException, DatabaseException
from app.utils.answer_checker import process_test_results
from app.crud.question import get_questions_by_test_id
from app.crud.test_access import update_test_access_status


async def create_result(db: AsyncSession, result_data: ResultCreate):
    """Создание результата теста и обновление статуса доступа"""
    try:
        test_result = await db.execute(select(Test).where(Test.id == result_data.test_id))
        test = test_result.scalar_one_or_none()
        if not test:
            raise NotFoundException(f"Тест с ID {result_data.test_id} не найден")
        user_result = await db.execute(select(User).where(User.id == result_data.user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundException(f"Пользователь с ID {result_data.user_id} не найден")
        questions = await get_questions_by_test_id(db, result_data.test_id)
        test_results = process_test_results(questions, result_data.answers, test.time_limit)
        for answer in test_results['checked_answers']:
            if isinstance(answer.get('time_start'), datetime):
                answer['time_start'] = answer['time_start'].isoformat()
            if isinstance(answer.get('time_end'), datetime):
                answer['time_end'] = answer['time_end'].isoformat()
        test_results['time_start'] = result_data.time_start.isoformat()
        test_results['time_end'] = result_data.time_end.isoformat()
        test_results['total_time_seconds'] = int((result_data.time_end - result_data.time_start).total_seconds())
        new_result = Result(
            test_id=result_data.test_id,
            user_id=result_data.user_id,
            score=test_results['total_score'],
            result=test_results
        )
        db.add(new_result)
        await db.flush()
        for answer in result_data.answers:
            question_result = await db.execute(select(Question).where(Question.id == answer.question_id))
            question = question_result.scalar_one_or_none()
            if not question:
                raise NotFoundException(f"Вопрос с ID {answer.question_id} не найден")
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
        # try:
        #     await update_test_access_status(
        #         db=db,
        #         test_id=result_data.test_id,
        #         user_id=result_data.user_id,
        #         is_passed=test_results['is_passed']
        #     )
        # except Exception:
        #     pass
        await db.commit()
        await db.refresh(new_result)
        return new_result
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при сохранении результата: {str(e)}")


async def get_result(db: AsyncSession, result_id: int):
    """Получение результата по id"""
    try:
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
    """Получение всех результатов пользователя"""
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
    """Получение всех результатов по тесту"""
    try:
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
    """Получение всех результатов"""
    try:
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


async def get_analytics_user_performance(db: AsyncSession) -> List[dict]:
    """Получение данных из представления analytics_user_performance"""
    try:
        # Выполняем запрос к представлению
        stmt = text("""
        SELECT 
            user_id,
            user_name,
            user_email,
            role_name,
            total_tests_accessed,
            total_tests_completed,
            avg_score,
            best_score,
            worst_score,
            total_attempts,
            avg_percent_completion,
            total_questions_answered,
            first_test_date,
            last_test_date,
            days_active
        FROM analytics_user_performance
        ORDER BY user_name
        """)
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        # Преобразуем результаты в список словарей
        analytics_data = []
        for row in rows:
            analytics_data.append({
                "user_id": row[0],
                "user_name": row[1],
                "user_email": row[2],
                "role_name": row[3],
                "total_tests_accessed": row[4] or 0,
                "total_tests_completed": row[5] or 0,
                "avg_score": float(row[6]) if row[6] is not None else 0.0,
                "best_score": row[7] or 0,
                "worst_score": row[8] or 0,
                "total_attempts": row[9] or 0,
                "avg_percent_completion": float(row[10]) if row[10] is not None else 0.0,
                "total_questions_answered": row[11] or 0,
                "first_test_date": row[12],
                "last_test_date": row[13],
                "days_active": row[14] or 0
            })
        
        return analytics_data
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении аналитических данных: {str(e)}")
