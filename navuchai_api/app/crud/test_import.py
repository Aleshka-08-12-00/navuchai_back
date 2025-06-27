from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload
import logging

from app.models import Test, Category, Question, TestQuestion, QuestionType, Locale, TestStatus
from app.schemas.test_import import TestImportData, QuestionImportData, TestImportResponse
from app.schemas.test import TestCreate
from app.schemas.question import QuestionCreate
from app.exceptions import NotFoundException, DatabaseException, BadRequestException
from app.utils.excel_parser import ExcelTestParser
import tempfile
import os
from datetime import datetime

logger = logging.getLogger(__name__)


async def import_test_from_excel(
    db: AsyncSession, 
    file_path: str, 
    creator_id: int
) -> TestImportResponse:
    """
    Импортирует тест из Excel файла
    
    Args:
        db: Сессия базы данных
        file_path: Путь к Excel файлу
        creator_id: ID создателя теста
        
    Returns:
        TestImportResponse: Результат импорта
        
    Raises:
        DatabaseException: При ошибке базы данных
        BadRequestException: При некорректных данных
    """
    try:
        logger.info(f"Начинаем импорт теста из Excel файла: {file_path}")
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            raise BadRequestException(f"Файл не найден: {file_path}")
        
        # Парсим Excel файл
        parser = ExcelTestParser()
        test_data = parser.parse_excel_file(file_path)
        
        logger.info(f"Excel файл успешно распарсен, найдено {len(test_data.questions)} вопросов")
        
        # Импортируем тест
        return await _import_test_data(db, test_data, creator_id)
        
    except (BadRequestException, DatabaseException):
        raise
    except Exception as e:
        logger.error(f"Ошибка при импорте из Excel: {str(e)}")
        raise DatabaseException(f"Ошибка при импорте из Excel: {str(e)}")


async def _import_test_data(
    db: AsyncSession, 
    test_data: TestImportData, 
    creator_id: int
) -> TestImportResponse:
    """
    Импортирует данные теста в базу данных
    
    Args:
        db: Сессия базы данных
        test_data: Данные для импорта
        creator_id: ID создателя теста
        
    Returns:
        TestImportResponse: Результат импорта
    """
    errors = []
    
    try:
        logger.info(f"Импортируем тест: {test_data.title}")
        
        # Находим или создаем категорию
        category = await _get_or_create_category(db, test_data.category_name)
        
        # Находим локаль
        locale = await _get_locale(db, test_data.locale_code)
        
        # Находим статус теста (по умолчанию - активный)
        test_status = await _get_default_test_status(db)
        
        # Создаем тест
        test_create = TestCreate(
            title=test_data.title,
            description=test_data.description,
            category_id=category.id,
            creator_id=creator_id,
            locale_id=locale.id,
            status_id=test_status.id,
            time_limit=test_data.time_limit,
            welcome_message=test_data.welcome_message,
            goodbye_message=test_data.goodbye_message,
            frozen=False,
            access_timestamp=datetime.utcnow()
        )
        
        new_test = await _create_test(db, test_create)
        logger.info(f"Тест создан с ID: {new_test.id}")
        
        # Импортируем вопросы
        imported_questions = 0
        for question_data in test_data.questions:
            try:
                await _import_question(db, new_test.id, question_data)
                imported_questions += 1
                logger.debug(f"Импортирован вопрос {question_data.position}")
            except Exception as e:
                error_msg = f"Ошибка при импорте вопроса {question_data.position}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        await db.commit()
        
        logger.info(f"Импорт завершен. Импортировано вопросов: {imported_questions}")
        
        return TestImportResponse(
            success=True,
            message=f"Тест '{test_data.title}' успешно импортирован",
            test_id=new_test.id,
            imported_questions=imported_questions,
            errors=errors
        )
        
    except Exception as e:
        await db.rollback()
        error_msg = f"Ошибка при импорте теста: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        return TestImportResponse(
            success=False,
            message=error_msg,
            errors=errors
        )


async def _get_or_create_category(db: AsyncSession, category_name: str) -> Category:
    """
    Находит или создает категорию
    
    Args:
        db: Сессия базы данных
        category_name: Название категории
        
    Returns:
        Category: Найденная или созданная категория
        
    Raises:
        DatabaseException: При ошибке базы данных
    """
    try:
        # Ищем существующую категорию
        result = await db.execute(
            select(Category).where(Category.name == category_name)
        )
        category = result.scalar_one_or_none()
        
        if category:
            logger.debug(f"Найдена существующая категория: {category_name}")
            return category
        
        # Создаем новую категорию
        logger.info(f"Создаем новую категорию: {category_name}")
        new_category = Category(name=category_name)
        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)
        return new_category
        
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Ошибка при работе с категорией '{category_name}': {str(e)}")
        raise DatabaseException(f"Ошибка при работе с категорией '{category_name}'")


async def _get_locale(db: AsyncSession, locale_code: str) -> Locale:
    """
    Находит локаль по коду
    
    Args:
        db: Сессия базы данных
        locale_code: Код локали
        
    Returns:
        Locale: Найденная локаль
        
    Raises:
        NotFoundException: Если локаль не найдена
        DatabaseException: При ошибке базы данных
    """
    try:
        result = await db.execute(
            select(Locale).where(Locale.code == locale_code)
        )
        locale = result.scalar_one_or_none()
        
        if not locale:
            logger.warning(f"Локаль с кодом '{locale_code}' не найдена")
            raise NotFoundException(f"Локаль с кодом '{locale_code}' не найдена")
        
        logger.debug(f"Найдена локаль: {locale_code}")
        return locale
        
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при поиске локали '{locale_code}': {str(e)}")
        raise DatabaseException(f"Ошибка при поиске локали '{locale_code}'")


async def _get_default_test_status(db: AsyncSession) -> TestStatus:
    """
    Получает статус теста по умолчанию (активный)
    
    Args:
        db: Сессия базы данных
        
    Returns:
        TestStatus: Статус теста по умолчанию
        
    Raises:
        NotFoundException: Если не найден ни один статус
        DatabaseException: При ошибке базы данных
    """
    try:
        # Ищем статус с кодом 'active' или ID 1
        result = await db.execute(
            select(TestStatus).where(TestStatus.id == 1)
        )
        status = result.scalar_one_or_none()
        
        if not status:
            # Если нет статуса с ID 1, берем первый доступный
            result = await db.execute(select(TestStatus))
            status = result.scalar_one_or_none()
            
            if not status:
                logger.error("Не найден ни один статус теста")
                raise NotFoundException("Не найден ни один статус теста")
        
        logger.debug(f"Используем статус теста: {status.id}")
        return status
        
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при поиске статуса теста: {str(e)}")
        raise DatabaseException("Ошибка при поиске статуса теста")


async def _create_test(db: AsyncSession, test_create: TestCreate) -> Test:
    """
    Создает новый тест
    
    Args:
        db: Сессия базы данных
        test_create: Данные для создания теста
        
    Returns:
        Test: Созданный тест
        
    Raises:
        DatabaseException: При ошибке создания теста
    """
    try:
        from app.crud.test import create_test
        return await create_test(db, test_create)
    except Exception as e:
        logger.error(f"Ошибка при создании теста: {str(e)}")
        raise DatabaseException(f"Ошибка при создании теста: {str(e)}")


async def _import_question(
    db: AsyncSession, 
    test_id: int, 
    question_data: QuestionImportData
) -> Question:
    """
    Импортирует вопрос в базу данных
    
    Args:
        db: Сессия базы данных
        test_id: ID теста
        question_data: Данные вопроса
        
    Returns:
        Question: Созданный вопрос
        
    Raises:
        DatabaseException: При ошибке создания вопроса
    """
    try:
        # Находим тип вопроса
        question_type = await _get_question_type(db, question_data.question_type)
        
        # Форматируем ответы
        answers_data = _format_question_answers(question_data)
        
        # Создаем вопрос
        question_create = QuestionCreate(
            text=question_data.question_text,
            text_abstract=question_data.question_abstract,
            type_id=question_type.id,
            reviewable=True,
            answers=answers_data,
            time_limit=question_data.time_limit
        )
        
        from app.crud.question import create_question
        question = await create_question(db, question_create)
        
        # Связываем вопрос с тестом
        test_question = TestQuestion(
            test_id=test_id,
            question_id=question.id,
            position=question_data.position,
            required=question_data.required,
            max_score=question_data.max_score
        )
        db.add(test_question)
        
        return question
        
    except Exception as e:
        logger.error(f"Ошибка при импорте вопроса: {str(e)}")
        raise DatabaseException(f"Ошибка при импорте вопроса: {str(e)}")


async def _get_question_type(db: AsyncSession, type_code: str) -> QuestionType:
    """
    Находит тип вопроса по коду
    
    Args:
        db: Сессия базы данных
        type_code: Код типа вопроса
        
    Returns:
        QuestionType: Найденный тип вопроса
        
    Raises:
        NotFoundException: Если тип вопроса не найден
        DatabaseException: При ошибке базы данных
    """
    try:
        result = await db.execute(
            select(QuestionType).where(QuestionType.code == type_code)
        )
        question_type = result.scalar_one_or_none()
        
        if not question_type:
            logger.warning(f"Тип вопроса с кодом '{type_code}' не найден")
            raise NotFoundException(f"Тип вопроса с кодом '{type_code}' не найден")
        
        return question_type
        
    except SQLAlchemyError as e:
        logger.error(f"Ошибка при поиске типа вопроса '{type_code}': {str(e)}")
        raise DatabaseException(f"Ошибка при поиске типа вопроса '{type_code}'")


def _format_question_answers(question_data: QuestionImportData) -> dict:
    """
    Форматирует ответы вопроса для сохранения в базу данных
    
    Args:
        question_data: Данные вопроса
        
    Returns:
        dict: Отформатированные ответы в нужном JSON формате
    """
    # Оборачиваем варианты ответов в HTML-теги
    all_answers = [f"<p>{option}</p>" for option in question_data.options]
    correct_answers = [f"<p>{answer}</p>" for answer in question_data.correct_answers]
    
    return {
        "settings": {
            "correctScore": question_data.max_score,
            "showMaxScore": True,
            "requireAnswer": True,
            "incorrectScore": 0,
            "stopIfIncorrect": False
        },
        "allAnswer": all_answers,
        "correctAnswer": correct_answers
    } 