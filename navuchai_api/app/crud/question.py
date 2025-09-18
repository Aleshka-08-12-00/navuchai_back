from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import update as sql_update, func

from app.models import Question, TestQuestion
from app.schemas.question import QuestionCreate, QuestionUpdate
from app.exceptions import NotFoundException, DatabaseException


# Получение списка вопросов
async def get_questions(db: AsyncSession):
    try:
        result = await db.execute(
            select(Question)
            .options(selectinload(Question.type))
            .order_by(Question.id)
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
            .order_by(TestQuestion.position)
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
        
        # Обновляем max_score во всех связанных TestQuestion записях
        if 'answers' in update_data:
            # Извлекаем correctScore из новых настроек вопроса
            answers = existing_question.answers
            correct_score = 1  # значение по умолчанию
            if isinstance(answers, dict) and 'settings' in answers:
                settings = answers.get('settings', {})
                correct_score = settings.get('correctScore', 1)
            
            # Обновляем все TestQuestion записи для этого вопроса
            await db.execute(
                sql_update(TestQuestion)
                .where(TestQuestion.question_id == question_id)
                .values(max_score=correct_score)
            )
            await db.commit()
        
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


async def update_question_positions(db: AsyncSession, test_id: int, positions_data: list):
    """
    Обновляет позиции вопросов в тесте.
    
    Args:
        db: Сессия базы данных
        test_id: ID теста
        positions_data: Список словарей с questionId и position
    """
    try:
        # update уже импортирован как sql_update
        
        # Проверяем, что все вопросы принадлежат данному тесту
        question_ids = [item["questionId"] for item in positions_data]
        
        # Получаем существующие связи вопросов с тестом
        result = await db.execute(
            select(TestQuestion)
            .where(TestQuestion.test_id == test_id)
            .where(TestQuestion.question_id.in_(question_ids))
        )
        existing_questions = result.scalars().all()
        
        if len(existing_questions) != len(question_ids):
            raise NotFoundException("Некоторые вопросы не найдены в данном тесте")
        
        # Обновляем позиции
        for item in positions_data:
            question_id = item["questionId"]
            position = item["position"]
            
            await db.execute(
                sql_update(TestQuestion)
                .where(TestQuestion.test_id == test_id)
                .where(TestQuestion.question_id == question_id)
                .values(position=position)
            )
        
        await db.commit()
        return {"message": "Позиции вопросов успешно обновлены"}
        
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении позиций вопросов: {str(e)}")
    except NotFoundException:
        raise
    except Exception as e:
        await db.rollback()
        raise DatabaseException(f"Неожиданная ошибка: {str(e)}")


# Копирование вопроса и привязка к тесту
async def copy_question_to_test(db: AsyncSession, source_question_id: int, target_test_id: int) -> Question:
    """
    Создаёт копию вопроса и привязывает её к указанному тесту на следующую позицию.
    """
    try:
        # 1) Получаем исходный вопрос
        result = await db.execute(
            select(Question).options(selectinload(Question.test_questions)).where(Question.id == source_question_id)
        )
        source_question = result.scalar_one_or_none()
        if not source_question:
            raise NotFoundException("Исходный вопрос не найден")

        # 2) Создаём копию вопроса
        new_question = Question(
            text=source_question.text,
            text_abstract=source_question.text_abstract,
            type_id=source_question.type_id,
            reviewable=source_question.reviewable,
            answers=source_question.answers,
            time_limit=source_question.time_limit
        )
        db.add(new_question)
        await db.commit()
        await db.refresh(new_question)

        # 3) Определяем следующую позицию в тесте
        pos_result = await db.execute(
            select(func.coalesce(func.max(TestQuestion.position), 0)).where(TestQuestion.test_id == target_test_id)
        )
        max_position = pos_result.scalar_one()
        next_position = (max_position or 0) + 1

        # 4) Определяем required и max_score
        required = True
        correct_score = 1
        answers = new_question.answers
        if isinstance(answers, dict) and 'settings' in answers:
            settings = answers.get('settings', {})
            correct_score = settings.get('correctScore', 1)

        # 5) Создаём связь TestQuestion
        link = TestQuestion(
            test_id=target_test_id,
            question_id=new_question.id,
            position=next_position,
            required=required,
            max_score=correct_score
        )
        db.add(link)
        await db.commit()
        # Перечитываем вопрос с предзагрузкой связей (например, type), чтобы корректно сериализовать ответ
        loaded_result = await db.execute(
            select(Question)
            .options(selectinload(Question.type))
            .where(Question.id == new_question.id)
        )
        return loaded_result.scalar_one()
    except NotFoundException:
        raise
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при копировании вопроса в тест")
    except Exception as e:
        await db.rollback()
        raise DatabaseException(f"Неожиданная ошибка при копировании вопроса: {str(e)}")
