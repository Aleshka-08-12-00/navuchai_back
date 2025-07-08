from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy import exists

from app.models import Test, Category, User, Locale, File, TestStatus, TestAccess, TestAccessStatus, Question, TestQuestion
from app.models.test import TestAccessEnum
from app.schemas.test import TestCreate, TestUpdate
from app.utils import format_test_with_names
from app.exceptions import NotFoundException, DatabaseException


# Получение списка тестов
async def get_tests(db: AsyncSession):
    try:
        result = await db.execute(
            select(
                Test, Category.name, User.name, Locale.code, 
                TestStatus.name, TestStatus.name_ru, TestStatus.color
            )
            .join(Category, Test.category_id == Category.id)
            .join(User, Test.creator_id == User.id)
            .join(Locale, Test.locale_id == Locale.id)
            .join(TestStatus, Test.status_id == TestStatus.id)
            .options(selectinload(Test.image))
            .options(selectinload(Test.thumbnail))
        )
        rows = result.all()
        return [format_test_with_names(
            test, category_name, creator_name, locale_code, 
            status_name, status_name_ru, status_color
        ) for test, category_name, creator_name, locale_code, status_name, status_name_ru, status_color in rows]
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка тестов")


# Получение конкретного теста по ID
async def get_test(db: AsyncSession, test_id: int):
    try:
        result = await db.execute(
            select(Test)
            .options(
                selectinload(Test.image),
                selectinload(Test.thumbnail),
                selectinload(Test.category),
                selectinload(Test.creator),
                selectinload(Test.locale),
                selectinload(Test.status)
            )
            .where(Test.id == test_id)
        )
        test = result.scalar_one_or_none()
        if not test:
            raise NotFoundException("Тест не найден")
            
        return format_test_with_names(
            test,
            test.category.name,
            test.creator.name if test.creator else None,
            test.locale.code,
            test.status.name,
            test.status.name_ru,
            test.status.color
        )
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных теста")


async def get_test_by_id(db: AsyncSession, test_id: int):
    result = await db.execute(
        select(Test)
        .options(selectinload(Test.image))
        .where(Test.id == test_id)
    )
    return result.scalar_one_or_none()


# Создание нового теста
async def create_test(db: AsyncSession, test: TestCreate) -> Test:
    """
    Создает новый тест
    """
    try:
        new_test = Test(
            title=test.title,
            description=test.description,
            category_id=test.category_id,
            creator_id=test.creator_id,
            access_timestamp=test.access_timestamp,
            status_id=test.status_id,
            frozen=test.frozen,
            locale_id=test.locale_id,
            time_limit=test.time_limit,
            img_id=test.img_id,
            thumbnail_id=test.thumbnail_id,
            welcome_message=test.welcome_message,
            goodbye_message=test.goodbye_message,
            access=test.access
        )
        db.add(new_test)
        await db.commit()
        await db.refresh(new_test)
        return new_test
    except SQLAlchemyError as e:
        await db.rollback()
        print(f"Ошибка при создании теста: {str(e)}")
        raise DatabaseException(f"Ошибка при создании теста: {str(e)}")
    except Exception as e:
        await db.rollback()
        print(f"Неожиданная ошибка при создании теста: {str(e)}")
        raise DatabaseException(f"Неожиданная ошибка при создании теста: {str(e)}")


async def update_test(db: AsyncSession, test_id: int, test: TestUpdate) -> Test:
    """
    Обновляет существующий тест
    """
    try:
        result = await db.execute(select(Test).where(Test.id == test_id))
        existing_test = result.scalar_one_or_none()
        
        if not existing_test:
            raise NotFoundException("Тест не найден")
        
        update_data = test.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(existing_test, field, value)
        
        await db.commit()
        await db.refresh(existing_test)
        return existing_test
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при обновлении теста")


# Удаление теста
async def delete_test(db: AsyncSession, test_id: int):
    try:
        test = await get_test_by_id(db, test_id)
        if not test:
            raise NotFoundException("Тест не найден")

        await db.delete(test)
        await db.commit()

        # Удаляем вопросы, которые больше не связаны ни с одним тестом
        # Получаем все вопросы
        questions_result = await db.execute(select(Question))
        all_questions = questions_result.scalars().all()
        for question in all_questions:
            # Проверяем, есть ли связи с тестами
            test_question_exists = await db.execute(
                select(exists().where(TestQuestion.question_id == question.id))
            )
            if not test_question_exists.scalar():
                await db.delete(question)
        await db.commit()

        return test
    except SQLAlchemyError:
        await db.rollback()
        raise DatabaseException("Ошибка при удалении теста")


async def get_user_tests(db: AsyncSession, user_id: int):
    """Получение списка тестов, доступных пользователю"""
    try:
        user_result = await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundException(f"Пользователь с ID {user_id} не найден")
        
        # Админы видят все тесты
        if user.role and user.role.code == 'admin':
            return await get_tests(db)
        
        # Обычные пользователи видят только тесты, доступные им, исключая тесты со статусом ID 2 (Setup in progress)
        result = await db.execute(
            select(
                Test, Category.name, User.name, Locale.code, 
                TestStatus.name, TestStatus.name_ru, TestStatus.color,
                TestAccessStatus.name, TestAccessStatus.code, TestAccessStatus.color,
                TestAccess.completed_number, TestAccess.avg_percent,
                TestAccess.access_code, TestAccess.is_completed
            )
            .join(TestAccess, Test.id == TestAccess.test_id)
            .join(Category, Test.category_id == Category.id)
            .join(User, Test.creator_id == User.id)
            .join(Locale, Test.locale_id == Locale.id)
            .join(TestStatus, Test.status_id == TestStatus.id)
            .outerjoin(TestAccessStatus, TestAccess.status_id == TestAccessStatus.id)
            .options(selectinload(Test.image))
            .options(selectinload(Test.thumbnail))
            .where(TestAccess.user_id == user_id)
            .where(Test.status_id != 2)  # Исключаем тесты со статусом ID 2 (Setup in progress)
        )
        rows = result.all()
        return [format_test_with_names(
            test, category_name, creator_name, locale_code, 
            status_name, status_name_ru, status_color,
            access_status_name, access_status_code, access_status_color,
            user_completed, user_percent,
            access_code, is_completed
        ) for test, category_name, creator_name, locale_code, status_name, status_name_ru, status_color, access_status_name, access_status_code, access_status_color, user_completed, user_percent, access_code, is_completed in rows]
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка тестов пользователя")


async def get_test_by_code(db: AsyncSession, code: str):
    """Получение публичного теста по коду"""
    try:
        result = await db.execute(
            select(Test)
            .options(
                selectinload(Test.image),
                selectinload(Test.thumbnail),
                selectinload(Test.category),
                selectinload(Test.creator),
                selectinload(Test.locale),
                selectinload(Test.status)
            )
            .where(Test.code == code)
            .where(Test.access == TestAccessEnum.PUBLIC)
        )
        test = result.scalar_one_or_none()
        if not test:
            raise NotFoundException("Публичный тест с указанным кодом не найден")
            
        return format_test_with_names(
            test,
            test.category.name,
            test.creator.name if test.creator else None,
            test.locale.code,
            test.status.name,
            test.status.name_ru,
            test.status.color
        )
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных теста")


async def get_test_by_access_code(db: AsyncSession, access_code: str, user_id: int):
    """Получение приватного теста по access_code из таблицы test_access с проверкой доступа пользователя"""
    try:
        result = await db.execute(
            select(Test)
            .join(TestAccess, Test.id == TestAccess.test_id)
            .options(
                selectinload(Test.image),
                selectinload(Test.thumbnail),
                selectinload(Test.category),
                selectinload(Test.creator),
                selectinload(Test.locale),
                selectinload(Test.status)
            )
            .where(TestAccess.access_code == access_code)
            .where(Test.access == TestAccessEnum.PRIVATE)
            .where(TestAccess.user_id == user_id)
        )
        test = result.scalar_one_or_none()
        if not test:
            raise NotFoundException("Приватный тест с указанным кодом доступа не найден или у вас нет доступа к нему")
            
        return format_test_with_names(
            test,
            test.category.name,
            test.creator.name if test.creator else None,
            test.locale.code,
            test.status.name,
            test.status.name_ru,
            test.status.color
        )
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных теста")


async def get_test_universal(db: AsyncSession, identifier: str, current_user: User = None):
    """Универсальное получение теста по ID, публичному коду или приватному access_code"""
    try:
        # Проверяем, является ли identifier числом (ID теста)
        if identifier.isdigit():
            test_id = int(identifier)
            return await get_test(db, test_id)
        
        # Проверяем публичный тест по коду
        result = await db.execute(
            select(Test)
            .options(
                selectinload(Test.image),
                selectinload(Test.thumbnail),
                selectinload(Test.category),
                selectinload(Test.creator),
                selectinload(Test.locale),
                selectinload(Test.status)
            )
            .where(Test.code == identifier)
            .where(Test.access == TestAccessEnum.PUBLIC)
        )
        test = result.scalar_one_or_none()
        if test:
            return format_test_with_names(
                test,
                test.category.name,
                test.creator.name if test.creator else None,
                test.locale.code,
                test.status.name,
                test.status.name_ru,
                test.status.color
            )
        
        # Проверяем приватный тест по access_code (требует авторизации)
        if not current_user:
            raise NotFoundException("Тест не найден или требует авторизации")
        
        # Проверяем роль пользователя
        user_result = await db.execute(
            select(User).options(selectinload(User.role)).where(User.id == current_user.id)
        )
        user = user_result.scalar_one_or_none()
        is_admin_or_moderator = user and user.role and user.role.code in ['admin', 'moderator']
        
        # Базовый запрос для поиска теста по access_code
        query = (
            select(Test)
            .join(TestAccess, Test.id == TestAccess.test_id)
            .options(
                selectinload(Test.image),
                selectinload(Test.thumbnail),
                selectinload(Test.category),
                selectinload(Test.creator),
                selectinload(Test.locale),
                selectinload(Test.status)
            )
            .where(TestAccess.access_code == identifier)
            .where(Test.access == TestAccessEnum.PRIVATE)
        )
        
        # Если не админ/модератор, добавляем проверку на назначение пользователя
        if not is_admin_or_moderator:
            query = query.where(TestAccess.user_id == current_user.id)
        
        result = await db.execute(query)
        test = result.scalar_one_or_none()
        if test:
            return format_test_with_names(
                test,
                test.category.name,
                test.creator.name if test.creator else None,
                test.locale.code,
                test.status.name,
                test.status.name_ru,
                test.status.color
            )
        
        raise NotFoundException("Тест не найден")
        
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных теста")
