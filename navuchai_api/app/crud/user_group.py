from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload
import csv
import io
import logging
from typing import List, Dict, Any

from app.models import UserGroup, UserGroupMember, User, TestGroupTest
from app.schemas.user_group import UserGroupCreate, UserGroupUpdate
from app.schemas.user_auth import UserImportResult, UserImportResponse
from app.exceptions import NotFoundException, DatabaseException
from app.models.test_access import TestAccess
from app.models.test_group_access import TestGroupAccess
from app.auth import get_password_hash

logger = logging.getLogger(__name__)


async def create_group(db: AsyncSession, group_data: UserGroupCreate, creator_id: int) -> UserGroup:
    try:
        new_group = UserGroup(**group_data.dict(), creator_id=creator_id)
        db.add(new_group)
        await db.commit()
        await db.refresh(new_group)
        await db.refresh(new_group, ['members'])
        return new_group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании группы: {str(e)}")


async def get_group(db: AsyncSession, group_id: int) -> UserGroup:
    result = await db.execute(
        select(UserGroup)
        .options(selectinload(UserGroup.members))
        .where(UserGroup.id == group_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise NotFoundException("Группа не найдена")
    return group


async def get_groups(db: AsyncSession) -> list[UserGroup]:
    result = await db.execute(
        select(UserGroup)
        .options(selectinload(UserGroup.members))
        .order_by(UserGroup.id)
    )
    return result.scalars().all()


async def update_group(db: AsyncSession, group_id: int, group_data: UserGroupUpdate) -> UserGroup:
    try:
        group = await get_group(db, group_id)
        for key, value in group_data.dict(exclude_unset=True).items():
            setattr(group, key, value)
        await db.commit()
        await db.refresh(group)
        await db.refresh(group, ['members'])
        return group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении группы: {str(e)}")


async def delete_group(db: AsyncSession, group_id: int) -> UserGroup:
    try:
        group = await get_group(db, group_id)
        # Удаляем все доступы по user_group_id
        await db.execute(
            TestAccess.__table__.delete().where(TestAccess.user_group_id == group_id)
        )
        await db.delete(group)
        await db.commit()
        return group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении группы: {str(e)}")


async def add_group_member(db: AsyncSession, group_id: int, user_id: int) -> UserGroupMember:
    try:
        # Проверяем существование группы
        await get_group(db, group_id)

        # Проверяем существование пользователя
        user_result = await db.execute(select(User).where(User.id == user_id))
        if not user_result.scalar_one_or_none():
            raise NotFoundException(f"Пользователь с ID {user_id} не найден")

        member = UserGroupMember(user_id=user_id, group_id=group_id)
        db.add(member)
        await db.commit()
        await db.refresh(member)
        
        # Автоматически назначаем пользователя на группы тестов и тесты
        try:
            await assign_user_to_test_groups_and_tests(db, user_id, group_id)
        except Exception as e:
            logger.warning(f"Не удалось автоматически назначить пользователя на группы тестов: {str(e)}")
            # Не прерываем операцию, если не удалось назначить доступ к тестам
        
        return member
    except IntegrityError:
        await db.rollback()
        raise DatabaseException("Пользователь уже состоит в этой группе")
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при добавлении пользователя в группу: {str(e)}")


async def remove_group_member(db: AsyncSession, group_id: int, user_id: int) -> UserGroupMember:
    try:
        await get_group(db, group_id)
        result = await db.execute(
            select(UserGroupMember)
            .where(
                UserGroupMember.group_id == group_id,
                UserGroupMember.user_id == user_id
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundException("Пользователь не найден в группе")
        
        # Удаляем доступы к группам тестов и тестам
        try:
            await remove_user_from_test_groups_and_tests(db, user_id, group_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить доступы пользователя к группам тестов: {str(e)}")
            # Не прерываем операцию, если не удалось удалить доступы к тестам
        
        await db.delete(member)
        await db.commit()
        return member
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении пользователя из группы: {str(e)}")


async def is_user_in_group(db: AsyncSession, group_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(UserGroupMember).where(
            UserGroupMember.group_id == group_id,
            UserGroupMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def assign_user_to_test_groups_and_tests(db: AsyncSession, user_id: int, group_id: int):
    """
    Автоматически назначает пользователя на группы тестов и тесты, 
    к которым имеет доступ группа пользователей
    """
    try:
        # Получаем все группы тестов, к которым имеет доступ данная группа пользователей
        test_group_access_stmt = (
            select(TestGroupAccess)
            .where(TestGroupAccess.user_group_id == group_id)
            .distinct(TestGroupAccess.test_group_id)
        )
        test_group_access_result = await db.execute(test_group_access_stmt)
        test_group_accesses = test_group_access_result.scalars().all()
        
        if not test_group_accesses:
            logger.info(f"Группа пользователей {group_id} не имеет доступа к группам тестов")
            return
        
        # Для каждой группы тестов создаем доступ для пользователя
        for test_group_access in test_group_accesses:
            test_group_id = test_group_access.test_group_id
            
            # Проверяем, есть ли уже доступ у пользователя к этой группе тестов
            existing_group_access = await db.execute(
                select(TestGroupAccess).where(
                    TestGroupAccess.test_group_id == test_group_id,
                    TestGroupAccess.user_id == user_id
                )
            )
            
            if not existing_group_access.scalar_one_or_none():
                # Создаем доступ к группе тестов
                new_test_group_access = TestGroupAccess(
                    test_group_id=test_group_id,
                    user_id=user_id,
                    user_group_id=group_id,
                    status_id=test_group_access.status_id,
                    start_date=test_group_access.start_date,
                    end_date=test_group_access.end_date
                )
                db.add(new_test_group_access)
                logger.info(f"Создан доступ пользователя {user_id} к группе тестов {test_group_id}")
            
            # Получаем все тесты в этой группе тестов
            test_group_tests_stmt = (
                select(TestGroupTest)
                .where(TestGroupTest.test_group_id == test_group_id)
            )
            test_group_tests_result = await db.execute(test_group_tests_stmt)
            test_group_tests = test_group_tests_result.scalars().all()
            
            # Для каждого теста создаем доступ для пользователя
            for test_group_test in test_group_tests:
                test_id = test_group_test.test_id
                
                # Проверяем, есть ли уже доступ у пользователя к этому тесту
                existing_test_access = await db.execute(
                    select(TestAccess).where(
                        TestAccess.test_id == test_id,
                        TestAccess.user_id == user_id
                    )
                )
                
                if not existing_test_access.scalar_one_or_none():
                    # Создаем доступ к тесту
                    new_test_access = TestAccess(
                        test_id=test_id,
                        user_id=user_id,
                        user_group_id=group_id,
                        test_group_id=test_group_id,
                        status_id=test_group_access.status_id if test_group_access.status_id else 1,
                        start_date=test_group_access.start_date,
                        end_date=test_group_access.end_date,
                        completed_number=0,
                        avg_percent=0,
                        is_completed=False
                    )
                    db.add(new_test_access)
                    logger.info(f"Создан доступ пользователя {user_id} к тесту {test_id}")
        
        await db.commit()
        logger.info(f"Пользователь {user_id} успешно назначен на все группы тестов и тесты группы {group_id}")
        
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Ошибка при назначении пользователя на группы тестов: {str(e)}")
        raise DatabaseException(f"Ошибка при назначении пользователя на группы тестов: {str(e)}")


async def remove_user_from_test_groups_and_tests(db: AsyncSession, user_id: int, group_id: int):
    """
    Удаляет доступ пользователя к группам тестов и тестам при удалении из группы пользователей
    """
    try:
        # Удаляем доступы к тестам, которые были созданы через эту группу пользователей
        await db.execute(
            TestAccess.__table__.delete().where(
                (TestAccess.user_id == user_id) & 
                (TestAccess.user_group_id == group_id)
            )
        )
        
        # Удаляем доступы к группам тестов, которые были созданы через эту группу пользователей
        await db.execute(
            TestGroupAccess.__table__.delete().where(
                (TestGroupAccess.user_id == user_id) & 
                (TestGroupAccess.user_group_id == group_id)
            )
        )
        
        await db.commit()
        logger.info(f"Удалены доступы пользователя {user_id} к группам тестов и тестам группы {group_id}")
        
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Ошибка при удалении доступа пользователя к группам тестов: {str(e)}")
        raise DatabaseException(f"Ошибка при удалении доступа пользователя к группам тестов: {str(e)}")


async def import_users_from_csv(
    db: AsyncSession, 
    csv_content: str, 
    group_id: int, 
    default_role_id: int = 3
) -> UserImportResponse:
    """
    Импортирует пользователей из CSV файла и добавляет их в группу
    
    Args:
        db: Сессия базы данных
        csv_content: Содержимое CSV файла
        group_id: ID группы для добавления пользователей
        default_role_id: ID роли по умолчанию для новых пользователей (по умолчанию 3)
        
    Returns:
        UserImportResponse: Результат импорта
    """
    try:
        # Проверяем существование группы
        await get_group(db, group_id)
        
        # Парсим CSV
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        # Проверяем обязательные колонки
        required_columns = ['email', 'name']
        if not all(col in reader.fieldnames for col in required_columns):
            raise DatabaseException("CSV должен содержать колонки: email, name")
        
        # Проверяем наличие колонки password (опционально)
        has_password_column = 'password' in reader.fieldnames
        
        results = []
        created_count = 0
        added_to_group_count = 0
        already_in_group_count = 0
        errors_count = 0
        
        for row in reader:
            try:
                email = row['email'].strip()
                name = row['name'].strip()
                password = row.get('password', '').strip() if has_password_column else None
                
                if not email or not name:
                    results.append(UserImportResult(
                        email=email or "N/A",
                        name=name or "N/A",
                        password=password,
                        action="error",
                        message="Отсутствует email или имя"
                    ))
                    errors_count += 1
                    continue
                
                # Ищем пользователя по email
                user_result = await db.execute(
                    select(User).where(User.email == email)
                )
                user = user_result.scalar_one_or_none()
                
                if user:
                    # Пользователь существует, проверяем членство в группе
                    if await is_user_in_group(db, group_id, user.id):
                        results.append(UserImportResult(
                            email=email,
                            name=name,
                            password=password,
                            action="already_in_group",
                            message="Пользователь уже состоит в группе"
                        ))
                        already_in_group_count += 1
                    else:
                        # Добавляем в группу
                        try:
                            await add_group_member(db, group_id, user.id)
                            results.append(UserImportResult(
                                email=email,
                                name=name,
                                password=password,
                                action="added_to_group",
                                message="Пользователь добавлен в группу"
                            ))
                            added_to_group_count += 1
                        except Exception as e:
                            results.append(UserImportResult(
                                email=email,
                                name=name,
                                password=password,
                                action="error",
                                message=f"Ошибка при добавлении в группу: {str(e)}"
                            ))
                            errors_count += 1
                else:
                    # Создаем нового пользователя
                    try:
                        # Генерируем username из email
                        username = email.split('@')[0]
                        
                        # Проверяем уникальность username
                        username_result = await db.execute(
                            select(User).where(User.username == username)
                        )
                        if username_result.scalar_one_or_none():
                            # Добавляем случайный суффикс
                            import random
                            username = f"{username}_{random.randint(1000, 9999)}"
                        
                        # Используем пароль из CSV или "1234" по умолчанию
                        user_password = password if password else "1234"
                        hashed_password = get_password_hash(user_password)
                        new_user = User(
                            name=name,
                            email=email,
                            password=hashed_password,
                            username=username,
                            role_id=default_role_id,
                            img_id=174,  # Значение по умолчанию для img_id
                            thumbnail_id=175  # Значение по умолчанию для thumbnail_id
                        )
                        
                        db.add(new_user)
                        await db.commit()
                        await db.refresh(new_user)
                        
                        # Добавляем в группу
                        await add_group_member(db, group_id, new_user.id)
                        
                        results.append(UserImportResult(
                            email=email,
                            name=name,
                            password=password,
                            action="created",
                            message=f"Пользователь создан и добавлен в группу (пароль: {user_password})"
                        ))
                        created_count += 1
                        
                    except Exception as e:
                        await db.rollback()
                        results.append(UserImportResult(
                            email=email,
                            name=name,
                            password=password,
                            action="error",
                            message=f"Ошибка при создании пользователя: {str(e)}"
                        ))
                        errors_count += 1
                        
            except Exception as e:
                password = row.get('password', '') if has_password_column else None
                results.append(UserImportResult(
                    email=row.get('email', 'N/A'),
                    name=row.get('name', 'N/A'),
                    password=password,
                    action="error",
                    message=f"Ошибка обработки строки: {str(e)}"
                ))
                errors_count += 1
        
        total_processed = len(results)
        success = errors_count == 0
        
        return UserImportResponse(
            success=success,
            total_processed=total_processed,
            created=created_count,
            added_to_group=added_to_group_count,
            already_in_group=already_in_group_count,
            errors=errors_count,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Ошибка при импорте пользователей: {str(e)}")
        raise DatabaseException(f"Ошибка при импорте пользователей: {str(e)}")