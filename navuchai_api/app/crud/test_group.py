from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from app.models.test_group import TestGroup
from app.models.test_group_test import TestGroupTest
from app.schemas.test_group import TestGroupCreate, TestGroupUpdate
from app.schemas.test_group_test import TestGroupTestCreate
from app.exceptions import DatabaseException, NotFoundException
from app.models import Test, Category, User, Locale, TestStatus
from app.models.test_group_access import TestGroupAccess
from app.models.test_access import TestAccess
from app.utils import format_test_with_names


# Получение списка всех групп
async def get_test_groups(db: AsyncSession):
    try:
        stmt = select(TestGroup).options(
            selectinload(TestGroup.status),
            selectinload(TestGroup.img),
            selectinload(TestGroup.thumbnail)
        ).order_by(TestGroup.id)
        result = await db.execute(stmt)
        groups = result.scalars().all()
        enriched = []
        for group in groups:
            group_dict = {k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                          for k, v in group.__dict__.items()
                          if not k.startswith('_')
                          and k not in {'status', 'img', 'thumbnail'}
                          and not isinstance(v, (dict, list, set, tuple))}
            if hasattr(group, 'status') and group.status:
                group_dict['status_name'] = group.status.name
                group_dict['status_name_ru'] = group.status.name_ru
                group_dict['status_color'] = group.status.color
            else:
                group_dict['status_name'] = None
                group_dict['status_name_ru'] = None
                group_dict['status_color'] = None
            group_dict['image'] = group.img.path if hasattr(group, 'img') and group.img else None
            group_dict['thumbnail'] = group.thumbnail.path if hasattr(group, 'thumbnail') and group.thumbnail else None
            enriched.append(group_dict)
        return enriched
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении списка групп: {str(e)}")


# Получение списка всех активных групп
async def get_active_test_groups(db: AsyncSession):
    try:
        
        stmt = (
            select(TestGroup)
            .join(TestStatus, TestGroup.status_id == TestStatus.id)
            .where(TestStatus.code == 'active')
            .options(
                selectinload(TestGroup.status),
                selectinload(TestGroup.img),
                selectinload(TestGroup.thumbnail)
            )
            .order_by(TestGroup.id)
        )
        result = await db.execute(stmt)
        groups = result.scalars().all()
        enriched = []
        for group in groups:
            group_dict = {k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                          for k, v in group.__dict__.items()
                          if not k.startswith('_')
                          and k not in {'status', 'img', 'thumbnail'}
                          and not isinstance(v, (dict, list, set, tuple))}
            if hasattr(group, 'status') and group.status:
                group_dict['status_name'] = group.status.name
                group_dict['status_name_ru'] = group.status.name_ru
                group_dict['status_color'] = group.status.color
            else:
                group_dict['status_name'] = None
                group_dict['status_name_ru'] = None
                group_dict['status_color'] = None
            group_dict['image'] = group.img.path if hasattr(group, 'img') and group.img else None
            group_dict['thumbnail'] = group.thumbnail.path if hasattr(group, 'thumbnail') and group.thumbnail else None
            enriched.append(group_dict)
        return enriched
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении списка активных групп: {str(e)}")


# Получение списка групп тестов с учетом доступа пользователя
async def get_test_groups_by_user_access(db: AsyncSession, user_id: int, user_role_code: str):
    try:
        # Для root возвращаем все группы
        if user_role_code == 'root':
            return await get_test_groups(db)
        
        # Для модератора возвращаем группы, к которым у него есть доступ + группу "Все тесты" (ID: 25)
        if user_role_code == 'moderator':
            stmt = (
                select(TestGroup)
                .outerjoin(TestGroupAccess, TestGroup.id == TestGroupAccess.test_group_id)
                .join(TestStatus, TestGroup.status_id == TestStatus.id)
                .where(
                    (
                        (TestGroupAccess.user_id == user_id) |  # Группы, к которым есть доступ
                        (TestGroup.id == 25)  # Группа "Все тесты" всегда доступна модератору
                    )
                )
                .options(
                    selectinload(TestGroup.status),
                    selectinload(TestGroup.img),
                    selectinload(TestGroup.thumbnail)
                )
                .order_by(TestGroup.id)
            )
            result = await db.execute(stmt)
            groups = result.scalars().all()
            
            enriched = []
            for group in groups:
                group_dict = {k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                              for k, v in group.__dict__.items()
                              if not k.startswith('_')
                              and k not in {'status', 'img', 'thumbnail'}
                              and not isinstance(v, (dict, list, set, tuple))}
                if hasattr(group, 'status') and group.status:
                    group_dict['status_name'] = group.status.name
                    group_dict['status_name_ru'] = group.status.name_ru
                    group_dict['status_color'] = group.status.color
                else:
                    group_dict['status_name'] = None
                    group_dict['status_name_ru'] = None
                    group_dict['status_color'] = None
                group_dict['image'] = group.img.path if hasattr(group, 'img') and group.img else None
                group_dict['thumbnail'] = group.thumbnail.path if hasattr(group, 'thumbnail') and group.thumbnail else None
                enriched.append(group_dict)
            return enriched
        
        # Для админа возвращаем только группы, к которым у него есть доступ
        if user_role_code == 'admin':
            stmt = (
                select(TestGroup)
                .join(TestGroupAccess, TestGroup.id == TestGroupAccess.test_group_id)
                .where(TestGroupAccess.user_id == user_id)
                .options(
                    selectinload(TestGroup.status),
                    selectinload(TestGroup.img),
                    selectinload(TestGroup.thumbnail)
                )
                .order_by(TestGroup.id)
            )
            result = await db.execute(stmt)
            groups = result.scalars().all()
            
            enriched = []
            for group in groups:
                group_dict = {k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                              for k, v in group.__dict__.items()
                              if not k.startswith('_')
                              and k not in {'status', 'img', 'thumbnail'}
                              and not isinstance(v, (dict, list, set, tuple))}
                if hasattr(group, 'status') and group.status:
                    group_dict['status_name'] = group.status.name
                    group_dict['status_name_ru'] = group.status.name_ru
                    group_dict['status_color'] = group.status.color
                else:
                    group_dict['status_name'] = None
                    group_dict['status_name_ru'] = None
                    group_dict['status_color'] = None
                group_dict['image'] = group.img.path if hasattr(group, 'img') and group.img else None
                group_dict['thumbnail'] = group.thumbnail.path if hasattr(group, 'thumbnail') and group.thumbnail else None
                enriched.append(group_dict)
            return enriched
        
        # Для обычных пользователей возвращаем только группы, к которым у них есть доступ И со статусом active
        
        stmt = (
            select(TestGroup)
            .join(TestGroupAccess, TestGroup.id == TestGroupAccess.test_group_id)
            .join(TestStatus, TestGroup.status_id == TestStatus.id)
            .where(
                TestGroupAccess.user_id == user_id,
                TestStatus.code == 'active'
            )
            .options(
                selectinload(TestGroup.status),
                selectinload(TestGroup.img),
                selectinload(TestGroup.thumbnail)
            )
            .order_by(TestGroup.id)
        )
        result = await db.execute(stmt)
        groups = result.scalars().all()
        
        enriched = []
        for group in groups:
            group_dict = {k: (v.isoformat() if hasattr(v, 'isoformat') else v)
                          for k, v in group.__dict__.items()
                          if not k.startswith('_')
                          and k not in {'status', 'img', 'thumbnail'}
                          and not isinstance(v, (dict, list, set, tuple))}
            if hasattr(group, 'status') and group.status:
                group_dict['status_name'] = group.status.name
                group_dict['status_name_ru'] = group.status.name_ru
                group_dict['status_color'] = group.status.color
            else:
                group_dict['status_name'] = None
                group_dict['status_name_ru'] = None
                group_dict['status_color'] = None
            group_dict['image'] = group.img.path if hasattr(group, 'img') and group.img else None
            group_dict['thumbnail'] = group.thumbnail.path if hasattr(group, 'thumbnail') and group.thumbnail else None
            enriched.append(group_dict)
        return enriched
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении списка групп: {str(e)}")


# Получение одной группы
async def get_test_group(db: AsyncSession, group_id: int):
    try:
        stmt = select(TestGroup).where(TestGroup.id == group_id)
        result = await db.execute(stmt)
        group = result.scalar_one_or_none()
        if not group:
            raise NotFoundException("Группа не найдена")
        return group
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении группы: {str(e)}")


# Получение одной группы с проверкой доступа пользователя
async def get_test_group_with_access_check(db: AsyncSession, group_id: int, user_id: int, user_role_code: str):
    try:
        # Для root разрешаем доступ к любой группе
        if user_role_code == 'root':
            return await get_test_group(db, group_id)
        
        # Для модератора проверяем наличие доступа + доступ к группе "Все тесты" (ID: 25)
        if user_role_code == 'moderator':
            # Специальная логика для группы "Все тесты" (ID: 25)
            if group_id == 25:
                stmt = (
                    select(TestGroup)
                    .join(TestStatus, TestGroup.status_id == TestStatus.id)
                    .where(TestGroup.id == group_id)
                )
            else:
                # Для остальных групп проверяем наличие доступа
                stmt = (
                    select(TestGroup)
                    .outerjoin(TestGroupAccess, TestGroup.id == TestGroupAccess.test_group_id)
                    .join(TestStatus, TestGroup.status_id == TestStatus.id)
                    .where(
                        TestGroup.id == group_id,
                        TestGroupAccess.user_id == user_id
                    )
                )
            
            result = await db.execute(stmt)
            group = result.scalar_one_or_none()
            
            if not group:
                raise NotFoundException("Группа не найдена, у вас нет доступа к ней или группа неактивна")
            
            return group
        
        # Для админа проверяем наличие доступа к группе
        if user_role_code == 'admin':
            stmt = (
                select(TestGroup)
                .join(TestGroupAccess, TestGroup.id == TestGroupAccess.test_group_id)
                .where(
                    TestGroup.id == group_id,
                    TestGroupAccess.user_id == user_id
                )
            )
            result = await db.execute(stmt)
            group = result.scalar_one_or_none()
            
            if not group:
                raise NotFoundException("Группа не найдена или у вас нет доступа к ней")
            
            return group
        
        # Для обычных пользователей проверяем наличие доступа И статус active
        
        stmt = (
            select(TestGroup)
            .join(TestGroupAccess, TestGroup.id == TestGroupAccess.test_group_id)
            .join(TestStatus, TestGroup.status_id == TestStatus.id)
            .where(
                TestGroup.id == group_id,
                TestGroupAccess.user_id == user_id,
                TestStatus.code == 'active'
            )
        )
        result = await db.execute(stmt)
        group = result.scalar_one_or_none()
        
        if not group:
            raise NotFoundException("Группа не найдена, у вас нет доступа к ней или группа неактивна")
        
        return group
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении группы: {str(e)}")


# Создание группы
async def create_test_group(db: AsyncSession, group: TestGroupCreate):
    try:
        db_group = TestGroup(**group.dict())
        db.add(db_group)
        await db.commit()
        await db.refresh(db_group)
        
        # Автоматически назначаем доступ группам "Администраторы" (ID: 76) и "Модераторы" (ID: 78)
        try:
            from app.crud.test_access import create_group_test_group_access
            
            # Назначаем доступ группе "Администраторы"
            try:
                await create_group_test_group_access(db, db_group.id, 76, status_id=1)
                print(f"Доступ к группе тестов {db_group.id} назначен группе 'Администраторы'")
            except Exception as e:
                print(f"Предупреждение: не удалось назначить доступ к группе тестов {db_group.id} группе 'Администраторы': {str(e)}")
            
            # Назначаем доступ группе "Модераторы"
            try:
                await create_group_test_group_access(db, db_group.id, 78, status_id=1)
                print(f"Доступ к группе тестов {db_group.id} назначен группе 'Модераторы'")
            except Exception as e:
                print(f"Предупреждение: не удалось назначить доступ к группе тестов {db_group.id} группе 'Модераторы': {str(e)}")
            
        except Exception as e:
            # Если не удалось назначить доступ, логируем ошибку, но не прерываем создание группы
            print(f"Предупреждение: не удалось назначить доступ к группе тестов {db_group.id} группам Администраторы/Модераторы: {str(e)}")
        
        return db_group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при создании группы: {str(e)}")


# Обновление группы
async def update_test_group(db: AsyncSession, group_id: int, group: TestGroupUpdate):
    try:
        db_group = await get_test_group(db, group_id)
        for field, value in group.dict(exclude_unset=True).items():
            setattr(db_group, field, value)
        await db.commit()
        await db.refresh(db_group)
        return db_group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при обновлении группы: {str(e)}")


# Удаление группы
async def delete_test_group(db: AsyncSession, group_id: int):
    try:
        db_group = await get_test_group(db, group_id)
        await db.delete(db_group)
        await db.commit()
        return db_group
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении группы: {str(e)}")


# Добавление теста в группу
async def add_test_to_group(db: AsyncSession, data: TestGroupTestCreate):
    try:
        db_link = TestGroupTest(**data.dict())
        db.add(db_link)
        await db.commit()
        await db.refresh(db_link)
        return db_link
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при добавлении теста в группу: {str(e)}")


# Удаление теста из группы
async def remove_test_from_group(db: AsyncSession, test_id: int, group_id: int):
    from sqlalchemy import select
    from app.models.test_group_test import TestGroupTest
    try:
        stmt = select(TestGroupTest).where(
            TestGroupTest.test_id == test_id,
            TestGroupTest.test_group_id == group_id
        )
        result = await db.execute(stmt)
        link = result.scalar_one_or_none()
        if not link:
            raise NotFoundException("Связь теста с группой не найдена")
        await db.delete(link)
        await db.commit()
        return {"detail": "Тест удалён из группы"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении теста из группы: {str(e)}")


# Получение всех тестов по group_id (для админов и внутренних операций)
async def get_all_tests_by_group_id(db: AsyncSession, group_id: int):
    """Получение всех тестов в группе без учета пользователя (для админов и внутренних операций)"""
    try:
        # Получаем саму группу
        group_stmt = select(TestGroup).where(TestGroup.id == group_id)
        group_result = await db.execute(group_stmt)
        group_obj = group_result.scalar_one_or_none()
        
        stmt = (
            select(
                Test, Category.name, User.name, Locale.code,
                TestStatus.name, TestStatus.name_ru, TestStatus.color
            )
            .join(Category, Test.category_id == Category.id)
            .join(User, Test.creator_id == User.id)
            .join(Locale, Test.locale_id == Locale.id)
            .join(TestStatus, Test.status_id == TestStatus.id)
            .join(TestGroupTest, Test.id == TestGroupTest.test_id)
            .where(TestGroupTest.test_group_id == group_id)
            .options(selectinload(Test.image))
            .options(selectinload(Test.thumbnail))
            .order_by(Test.id)
        )
        result = await db.execute(stmt)
        rows = result.all()
        tests = []
        for test, category_name, creator_name, locale_code, status_name, status_name_ru, status_color in rows:
            # Используем format_test_with_names для правильного маппинга полей
            test_dict = format_test_with_names(
                test, category_name, creator_name, locale_code, 
                status_name, status_name_ru, status_color
            )
            
            # Добавляем информацию о группе
            test_dict['group'] = group_obj
            
            # Создаем объект TestWithDetails из словаря
            from app.schemas.test import TestWithDetails
            test_with_details = TestWithDetails(**test_dict)
            tests.append(test_with_details)
            
        return tests
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении тестов группы: {str(e)}")

# Получение тестов по group_id с полной инфой (возврат ORM-объектов для TestWithDetails)
async def get_tests_by_group_id(db: AsyncSession, group_id: int, user_id: int = None, user_role_code: str = None):
    try:
        # Получаем саму группу
        group_stmt = select(TestGroup).where(TestGroup.id == group_id)
        group_result = await db.execute(group_stmt)
        group_obj = group_result.scalar_one_or_none()
        
        # Для root используем данные из основной таблицы Test
        if user_role_code == 'root':
            stmt = (
                select(
                    Test, Category.name, User.name, Locale.code,
                    TestStatus.name, TestStatus.name_ru, TestStatus.color
                )
                .join(Category, Test.category_id == Category.id)
                .join(User, Test.creator_id == User.id)
                .join(Locale, Test.locale_id == Locale.id)
                .join(TestStatus, Test.status_id == TestStatus.id)
                .join(TestGroupTest, Test.id == TestGroupTest.test_id)
                .where(TestGroupTest.test_group_id == group_id)
                .options(selectinload(Test.image))
                .options(selectinload(Test.thumbnail))
                .order_by(Test.id)
            )
            result = await db.execute(stmt)
            rows = result.all()
            tests = []
            for test, category_name, creator_name, locale_code, status_name, status_name_ru, status_color in rows:
                # Используем format_test_with_names для правильного маппинга полей
                test_dict = format_test_with_names(
                    test, category_name, creator_name, locale_code, 
                    status_name, status_name_ru, status_color
                )
                
                # Добавляем информацию о группе
                test_dict['group'] = group_obj
                
                # Создаем объект TestWithDetails из словаря
                from app.schemas.test import TestWithDetails
                test_with_details = TestWithDetails(**test_dict)
                tests.append(test_with_details)
                
            return tests
        elif user_role_code == 'moderator':
            # Для модератора проверяем доступ к группе и используем данные из TestAccess (как обычные пользователи)
            # Специальная логика для группы "Все тесты" (ID: 25)
            if group_id == 25:
                # Для группы "Все тесты" не проверяем TestGroupAccess, сразу получаем тесты
                pass
            else:
                # Для остальных групп проверяем доступ к группе
                access_stmt = (
                    select(TestGroupAccess)
                    .join(TestGroup, TestGroupAccess.test_group_id == TestGroup.id)
                    .join(TestStatus, TestGroup.status_id == TestStatus.id)
                    .where(
                        TestGroupAccess.test_group_id == group_id,
                        TestGroupAccess.user_id == user_id,
                        TestStatus.code == 'active'
                    )
                )
                access_result = await db.execute(access_stmt)
                access = access_result.scalar_one_or_none()
                
                if not access:
                    raise NotFoundException("У вас нет доступа к этой группе или группа неактивна")
            
            # Если доступ есть, получаем тесты как для обычных пользователей
            from app.models import TestAccess, TestAccessStatus
            
            stmt = (
                select(
                    Test, Category.name, User.name, Locale.code,
                    TestStatus.name, TestStatus.name_ru, TestStatus.color,
                    TestAccessStatus.name, TestAccessStatus.code, TestAccessStatus.color,
                    TestAccess.completed_number, TestAccess.avg_percent,
                    TestAccess.access_code, TestAccess.is_completed
                )
                .join(Category, Test.category_id == Category.id)
                .join(User, Test.creator_id == User.id)
                .join(Locale, Test.locale_id == Locale.id)
                .join(TestStatus, Test.status_id == TestStatus.id)
                .join(TestGroupTest, Test.id == TestGroupTest.test_id)
                .join(TestAccess, Test.id == TestAccess.test_id)
                .outerjoin(TestAccessStatus, TestAccess.status_id == TestAccessStatus.id)
                .where(TestGroupTest.test_group_id == group_id)
                .where(TestAccess.user_id == user_id)
                .options(selectinload(Test.image))
                .options(selectinload(Test.thumbnail))
                .order_by(Test.id)
            )
            result = await db.execute(stmt)
            rows = result.all()
            tests = []
            for test, category_name, creator_name, locale_code, status_name, status_name_ru, status_color, access_status_name, access_status_code, access_status_color, user_completed, user_percent, access_code, is_completed in rows:
                # Используем format_test_with_names с данными из TestAccess
                test_dict = format_test_with_names(
                    test, category_name, creator_name, locale_code, 
                    status_name, status_name_ru, status_color,
                    access_status_name, access_status_code, access_status_color,
                    user_completed, user_percent, access_code, is_completed
                )
                
                # Добавляем информацию о группе
                test_dict['group'] = group_obj
                
                # Создаем объект TestWithDetails из словаря
                from app.schemas.test import TestWithDetails
                test_with_details = TestWithDetails(**test_dict)
                tests.append(test_with_details)
                
            return tests
        elif user_role_code == 'admin':
            # Для админа проверяем доступ к группе и используем данные из основной таблицы Test
            # Сначала проверяем, есть ли у админа доступ к группе
            access_stmt = (
                select(TestGroupAccess)
                .where(
                    TestGroupAccess.test_group_id == group_id,
                    TestGroupAccess.user_id == user_id
                )
            )
            access_result = await db.execute(access_stmt)
            access = access_result.scalar_one_or_none()
            
            if not access:
                raise NotFoundException("У вас нет доступа к этой группе")
            
            # Если доступ есть, получаем тесты как для root/moderator
            stmt = (
                select(
                    Test, Category.name, User.name, Locale.code,
                    TestStatus.name, TestStatus.name_ru, TestStatus.color
                )
                .join(Category, Test.category_id == Category.id)
                .join(User, Test.creator_id == User.id)
                .join(Locale, Test.locale_id == Locale.id)
                .join(TestStatus, Test.status_id == TestStatus.id)
                .join(TestGroupTest, Test.id == TestGroupTest.test_id)
                .where(TestGroupTest.test_group_id == group_id)
                .options(selectinload(Test.image))
                .options(selectinload(Test.thumbnail))
                .order_by(Test.id)
            )
            result = await db.execute(stmt)
            rows = result.all()
            tests = []
            for test, category_name, creator_name, locale_code, status_name, status_name_ru, status_color in rows:
                # Используем format_test_with_names для правильного маппинга полей
                test_dict = format_test_with_names(
                    test, category_name, creator_name, locale_code, 
                    status_name, status_name_ru, status_color
                )
                
                # Добавляем информацию о группе
                test_dict['group'] = group_obj
                
                # Создаем объект TestWithDetails из словаря
                from app.schemas.test import TestWithDetails
                test_with_details = TestWithDetails(**test_dict)
                tests.append(test_with_details)
                
            return tests
        else:
            # Для обычных пользователей используем данные из TestAccess
            from app.models import TestAccess, TestAccessStatus
            
            stmt = (
                select(
                    Test, Category.name, User.name, Locale.code,
                    TestStatus.name, TestStatus.name_ru, TestStatus.color,
                    TestAccessStatus.name, TestAccessStatus.code, TestAccessStatus.color,
                    TestAccess.completed_number, TestAccess.avg_percent,
                    TestAccess.access_code, TestAccess.is_completed
                )
                .join(Category, Test.category_id == Category.id)
                .join(User, Test.creator_id == User.id)
                .join(Locale, Test.locale_id == Locale.id)
                .join(TestStatus, Test.status_id == TestStatus.id)
                .join(TestGroupTest, Test.id == TestGroupTest.test_id)
                .join(TestAccess, Test.id == TestAccess.test_id)
                .outerjoin(TestAccessStatus, TestAccess.status_id == TestAccessStatus.id)
                .where(TestGroupTest.test_group_id == group_id)
                .where(TestAccess.user_id == user_id)
                .options(selectinload(Test.image))
                .options(selectinload(Test.thumbnail))
                .order_by(Test.id)
            )
            result = await db.execute(stmt)
            rows = result.all()
            tests = []
            for test, category_name, creator_name, locale_code, status_name, status_name_ru, status_color, access_status_name, access_status_code, access_status_color, user_completed, user_percent, access_code, is_completed in rows:
                # Используем format_test_with_names с данными из TestAccess
                test_dict = format_test_with_names(
                    test, category_name, creator_name, locale_code, 
                    status_name, status_name_ru, status_color,
                    access_status_name, access_status_code, access_status_color,
                    user_completed, user_percent, access_code, is_completed
                )
                
                # Добавляем информацию о группе
                test_dict['group'] = group_obj
                
                # Создаем объект TestWithDetails из словаря
                from app.schemas.test import TestWithDetails
                test_with_details = TestWithDetails(**test_dict)
                tests.append(test_with_details)
                
            return tests
            
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении тестов группы: {str(e)}")


# Получение групп тестов с категориями и тестами в древовидной структуре
async def get_test_groups_with_categories(db: AsyncSession, user_id: int, user_role_code: str):
    try:
        from sqlalchemy import func
        
        # Базовый запрос для получения групп с учетом доступа
        if user_role_code == 'root':
            # Для root - все группы
            group_stmt = (
                select(TestGroup)
                .options(
                    selectinload(TestGroup.status),
                    selectinload(TestGroup.img),
                    selectinload(TestGroup.thumbnail)
                )
                .order_by(TestGroup.id)
            )
        elif user_role_code == 'moderator':
            # Для модератора - доступные группы + группа "Все тесты" (ID: 25)
            group_stmt = (
                select(TestGroup)
                .outerjoin(TestGroupAccess, TestGroup.id == TestGroupAccess.test_group_id)
                .join(TestStatus, TestGroup.status_id == TestStatus.id)
                .where(
                    (
                        (TestGroupAccess.user_id == user_id) |  # Группы, к которым есть доступ
                        (TestGroup.id == 25)  # Группа "Все тесты" всегда доступна модератору
                    )
                )
                .options(
                    selectinload(TestGroup.status),
                    selectinload(TestGroup.img),
                    selectinload(TestGroup.thumbnail)
                )
                .order_by(TestGroup.id)
            )
        elif user_role_code == 'admin':
            # Для админа - только группы, к которым у него есть доступ
            group_stmt = (
                select(TestGroup)
                .join(TestGroupAccess, TestGroup.id == TestGroupAccess.test_group_id)
                .where(TestGroupAccess.user_id == user_id)
                .options(
                    selectinload(TestGroup.status),
                    selectinload(TestGroup.img),
                    selectinload(TestGroup.thumbnail)
                )
                .order_by(TestGroup.id)
            )
        else:
            # Для обычных пользователей - только доступные группы со статусом active
            
            group_stmt = (
                select(TestGroup)
                .join(TestGroupAccess, TestGroup.id == TestGroupAccess.test_group_id)
                .join(TestStatus, TestGroup.status_id == TestStatus.id)
                .where(
                    TestGroupAccess.user_id == user_id,
                    TestStatus.code == 'active'
                )
                .options(
                    selectinload(TestGroup.status),
                    selectinload(TestGroup.img),
                    selectinload(TestGroup.thumbnail)
                )
                .order_by(TestGroup.id)
            )
        
        result = await db.execute(group_stmt)
        groups = result.scalars().all()
        
        # Добавляем отладочную информацию для модераторов
        if user_role_code == 'moderator':
            print(f"DEBUG: get_test_groups_with_categories - Модератор {user_id} - найдено групп: {len(groups)}")
            for group in groups:
                print(f"DEBUG: get_test_groups_with_categories - Группа ID {group.id}, название: {group.name}")
        
        # Для каждой группы получаем тесты, сгруппированные по категориям
        result_groups = []
        
        for group in groups:
            # Получаем тесты для группы
            if user_role_code == 'moderator' and group.id == 25:
                # Для модератора в группе "Все тесты" показываем только тесты, к которым у него есть доступ
                tests_stmt = (
                    select(
                        Test, Category.id.label('category_id'), Category.name.label('category_name'),
                        TestStatus.name.label('status_name'), TestStatus.name_ru.label('status_name_ru'),
                        TestStatus.color.label('status_color'), TestAccess.is_completed.label('is_completed')
                    )
                    .join(Category, Test.category_id == Category.id)
                    .join(TestStatus, Test.status_id == TestStatus.id)
                    .join(TestGroupTest, Test.id == TestGroupTest.test_id)
                    .join(TestAccess, (Test.id == TestAccess.test_id) & (TestAccess.user_id == user_id))
                    .where(TestGroupTest.test_group_id == group.id)
                    .options(selectinload(Test.image), selectinload(Test.thumbnail))
                    .order_by(Category.id, Test.id)
                )
            else:
                # Для остальных случаев - обычная логика
                tests_stmt = (
                    select(
                        Test, Category.id.label('category_id'), Category.name.label('category_name'),
                        TestStatus.name.label('status_name'), TestStatus.name_ru.label('status_name_ru'),
                        TestStatus.color.label('status_color'), TestAccess.is_completed.label('is_completed')
                    )
                    .join(Category, Test.category_id == Category.id)
                    .join(TestStatus, Test.status_id == TestStatus.id)
                    .join(TestGroupTest, Test.id == TestGroupTest.test_id)
                    .outerjoin(TestAccess, (Test.id == TestAccess.test_id) & (TestAccess.user_id == user_id))
                    .where(TestGroupTest.test_group_id == group.id)
                    .options(selectinload(Test.image), selectinload(Test.thumbnail))
                    .order_by(Category.id, Test.id)
                )
            
            tests_result = await db.execute(tests_stmt)
            tests_data = tests_result.all()
            
            # Группируем тесты по категориям
            categories_dict = {}
            total_tests_count = 0
            
            for test, category_id, category_name, status_name, status_name_ru, status_color, is_completed in tests_data:
                if category_id not in categories_dict:
                    categories_dict[category_id] = {
                        'id': category_id,
                        'name': category_name,
                        'tests': [],
                        'tests_count': 0
                    }
                
                # Формируем объект теста
                test_dict = {
                    'id': test.id,
                    'title': test.title,
                    'description': test.description,
                    'time_limit': test.time_limit,
                    'avg_percent': test.avg_percent,
                    'completed_number': test.completed_number,
                    'access_timestamp': test.access_timestamp,
                    'frozen': test.frozen,
                    'created_at': test.created_at,
                    'updated_at': test.updated_at,
                    'image': test.image.path if test.image else None,
                    'thumbnail': test.thumbnail.path if test.thumbnail else None,
                    'status_name': status_name,
                    'status_name_ru': status_name_ru,
                    'status_color': status_color,
                    'is_completed': is_completed
                }
                
                categories_dict[category_id]['tests'].append(test_dict)
                categories_dict[category_id]['tests_count'] += 1
                total_tests_count += 1
            
            # Сортируем категории по ID и тесты внутри каждой категории по ID
            sorted_categories = []
            for category_id in sorted(categories_dict.keys()):
                category = categories_dict[category_id]
                # Сортируем тесты внутри категории по ID
                category['tests'] = sorted(category['tests'], key=lambda x: x['id'])
                sorted_categories.append(category)
            
            # Формируем объект группы
            group_dict = {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'date_start': group.date_start,
                'date_end': group.date_end,
                'time_limit': group.time_limit,
                'created_at': group.created_at,
                'updated_at': group.updated_at,
                'status_name': group.status.name if group.status else None,
                'status_name_ru': group.status.name_ru if group.status else None,
                'status_color': group.status.color if group.status else None,
                'image': group.img.path if group.img else None,
                'thumbnail': group.thumbnail.path if group.thumbnail else None,
                'categories': sorted_categories,
                'total_tests_count': total_tests_count
            }
            
            result_groups.append(group_dict)
        
        return result_groups
        
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении групп с категориями: {str(e)}")
