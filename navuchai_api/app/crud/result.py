from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.models import Result, UserAnswer, Test, Question, User
from app.schemas.result import ResultCreate
from app.exceptions import NotFoundException, DatabaseException


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

        # Создаем результат
        new_result = Result(
            test_id=result_data.test_id,
            user_id=result_data.user_id,
            score=result_data.score
        )
        db.add(new_result)
        await db.flush()  # Получаем ID результата

        # Создаем ответы пользователя
        for answer in result_data.answers:
            # Проверяем существование вопроса
            question_result = await db.execute(
                select(Question).where(Question.id == answer.question_id)
            )
            question = question_result.scalar_one_or_none()
            if not question:
                raise NotFoundException(f"Вопрос с ID {answer.question_id} не найден")

            new_answer = UserAnswer(
                result_id=new_result.id,
                question_id=answer.question_id,
                user_id=result_data.user_id,
                answer=answer.answer
            )
            db.add(new_answer)

        await db.commit()
        await db.refresh(new_result)

        return new_result

    except SQLAlchemyError as e:
        await db.rollback()
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
            return None

        return result_obj
    except SQLAlchemyError as e:
        print(f"Ошибка при получении результата: {str(e)}")
        raise DatabaseException(f"Ошибка при получении результата: {str(e)}")


async def get_user_results(db: AsyncSession, user_id: int):
    try:
        # Получаем результаты с ответами
        stmt = (
            select(Result)
            .options(selectinload(Result.user_answers))
            .where(Result.user_id == user_id)
        )
        result = await db.execute(stmt)
        results = result.scalars().all()

        return results
    except SQLAlchemyError as e:
        print(f"Ошибка при получении результатов пользователя: {str(e)}")
        raise DatabaseException(f"Ошибка при получении результатов пользователя: {str(e)}")


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
        print(f"Ошибка при получении результатов теста: {str(e)}")
        raise DatabaseException(f"Ошибка при получении результатов теста: {str(e)}")
