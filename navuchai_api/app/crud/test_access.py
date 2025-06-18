from datetime import datetime
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import secrets

from app.models.test_access import TestAccess
from app.models.user_group_member import UserGroupMember
from app.models.test_access_status import TestAccessStatus
from app.models.test_status import TestStatus
from app.models.test import Test, TestAccessEnum
from app.schemas.test_access import TestAccessCreate
from app.exceptions import DatabaseException, NotFoundException
from app.models.user import User
from app.models.user_group import UserGroup

OPAQUE_TOKEN_NUM_BYTES = 16


def _generate_access_code() -> str:
    return secrets.token_urlsafe(OPAQUE_TOKEN_NUM_BYTES)


async def create_test_access(db: AsyncSession, test_access_data: TestAccessCreate) -> TestAccess:
    """Создание доступа к тесту для одного пользователя"""
    try:
        test_result = await db.execute(select(Test).where(Test.id == test_access_data.test_id))
        test = test_result.scalar_one_or_none()
        if not test:
            raise NotFoundException(f"Тест с ID {test_access_data.test_id} не найден")

        # Проверяем, что статус передан и существует
        if not test_access_data.status_id:
            raise NotFoundException("status_id обязателен для создания доступа к тесту")
        status_result = await db.execute(
            select(TestAccessStatus).where(TestAccessStatus.id == test_access_data.status_id)
        )
        status = status_result.scalar_one_or_none()
        if not status:
            raise NotFoundException(f"Статус с ID {test_access_data.status_id} не найден")

        data_for_model = test_access_data.model_dump(exclude_none=True)
        data_for_model.pop('access_code', None)
        data_for_model['completed_number'] = 0
        data_for_model['avg_percent'] = 0
        db_test_access = TestAccess(**data_for_model)

        if test_access_data.user_id:
            db_test_access.access_code = _generate_access_code()

        db.add(db_test_access)
        await db.commit()
        
        # Загружаем созданную запись со всеми связанными сущностями
        result = await db.execute(
            select(TestAccess)
            .options(
                selectinload(TestAccess.user),
                selectinload(TestAccess.test),
                selectinload(TestAccess.status)
            )
            .where(TestAccess.id == db_test_access.id)
        )
        test_access = result.scalar_one()
        
        # Проверяем, что статус загружен
        if test_access and test_access.status:
            print(f"Debug: Status loaded - {test_access.status.name}, {test_access.status.code}, {test_access.status.color}")
        else:
            print("Debug: Status not loaded")
            
        return test_access
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при создании доступа к тесту: {str(e)}")
    except Exception as e:
        raise DatabaseException(f"Неожиданная ошибка при создании доступа к тесту: {str(e)}")


async def create_group_test_access(db: AsyncSession, test_id: int, group_id: int, start_date: datetime = None, end_date: datetime = None, status_id: int = None) -> list[TestAccess]:
    """Создание доступа к тесту для группы пользователей"""
    try:
        if status_id:
            status_result = await db.execute(select(TestStatus).where(TestStatus.id == status_id))
            status = status_result.scalar_one_or_none()
            if not status:
                raise NotFoundException(f"Статус с ID {status_id} не найден")

        query = select(UserGroupMember).where(UserGroupMember.group_id == group_id)
        result = await db.execute(query)
        group_members = result.scalars().all()
        if not group_members:
            raise NotFoundException(f"В группе с ID {group_id} нет пользователей")

        users_with_access = []
        for member in group_members:
            existing_access = await get_test_access(db, test_id, member.user_id)
            if existing_access:
                users_with_access.append(member.user_id)

        if users_with_access:
            raise DatabaseException(
                f"Следующие пользователи уже имеют доступ к тесту {test_id}: {users_with_access}. "
                "Удалите существующие доступы перед добавлением группового доступа."
            )

        created_accesses = []
        for member in group_members:
            test_access_payload = TestAccessCreate(
                test_id=test_id,
                user_id=member.user_id,
                group_id=group_id,
                start_date=start_date,
                end_date=end_date,
                status_id=status_id if status_id is not None else 1
            )
            created_access = await create_test_access(db, test_access_payload)
            created_accesses.append(created_access)
        return created_accesses
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при создании группового доступа к тесту: {str(e)}")


async def get_test_access(db: AsyncSession, test_id: int, user_id: int) -> TestAccess:
    """Получение информации о доступе пользователя к тесту (по test_id и user_id)"""
    try:
        query = select(TestAccess).where(
            TestAccess.test_id == test_id,
            TestAccess.user_id == user_id
        ).options(selectinload(TestAccess.status))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении информации о доступе к тесту")


async def update_test_access(db: AsyncSession, test_id: int, access: str) -> Test:
    """Изменение значения access в тесте"""
    try:
        if access not in ['public', 'private']:
            raise ValueError("Значение access должно быть 'public' или 'private'")
        query = select(Test).where(Test.id == test_id)
        result = await db.execute(query)
        test = result.scalar_one_or_none()
        if not test:
            raise NotFoundException(f"Тест с ID {test_id} не найден")
        stmt = update(Test).where(Test.id == test_id).values(access=access)
        await db.execute(stmt)
        await db.commit()
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении доступа к тесту")
    except ValueError as e:
        raise DatabaseException(str(e))


async def get_test_access_code(db: AsyncSession, test_id: int, user_id: int) -> dict:
    """Получение кода доступа к тесту"""
    test = await db.execute(select(Test).where(Test.id == test_id))
    test = test.scalar_one_or_none()
    if not test:
        raise NotFoundException(f"Тест с id {test_id} не найден")
    if test.access == TestAccessEnum.PUBLIC:
        return {"code": test.code}
    test_access = await db.execute(select(TestAccess).where(TestAccess.test_id == test_id, TestAccess.user_id == user_id))
    test_access = test_access.scalar_one_or_none()
    if not test_access:
        raise NotFoundException(f"Доступ к тесту {test_id} для пользователя {user_id} не найден")
    return {"access_code": test_access.access_code}


async def update_test_access_status(db: AsyncSession, test_id: int, user_id: int, is_passed: bool) -> TestAccess:
    """Обновление статуса доступа к тесту в зависимости от результата"""
    try:
        test_access = await get_test_access(db, test_id, user_id)
        if not test_access:
            raise NotFoundException(f"Доступ к тесту {test_id} для пользователя {user_id} не найден")
        status_result = await db.execute(
            select(TestAccessStatus).where(TestAccessStatus.code.in_(['COMPLETED', 'FAILED']))
        )
        statuses = {s.code: s for s in status_result.scalars().all()}
        if not statuses:
            raise NotFoundException("Статусы доступа 'COMPLETED' и 'FAILED' не найдены")
        new_status = statuses['COMPLETED'] if is_passed else statuses['FAILED']
        test_access.status_id = new_status.id
        await db.commit()
        await db.refresh(test_access)
        return test_access
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при обновлении статуса доступа: {str(e)}")


async def get_all_test_accesses(db: AsyncSession):
    """Получить все доступы пользователей к тестам с деталями пользователя и теста"""
    try:
        result = await db.execute(
            select(TestAccess)
            .options(selectinload(TestAccess.user))
            .options(selectinload(TestAccess.test))
            .options(selectinload(TestAccess.status))
        )
        return result.scalars().all()
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении списка доступов: {str(e)}")


async def delete_test_access(db: AsyncSession, test_id: int, user_id: int):
    """Удалить доступ пользователя к тесту"""
    try:
        access = await get_test_access(db, test_id, user_id)
        if not access:
            raise NotFoundException(f"Доступ к тесту {test_id} для пользователя {user_id} не найден")
        await db.delete(access)
        await db.commit()
        return {"detail": "Доступ удалён"}
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при удалении доступа: {str(e)}")


async def delete_group_test_access(db: AsyncSession, test_id: int, group_id: int):
    """Удалить доступ к тесту для всей группы"""
    try:
        # Находим все записи доступа для данной группы и теста
        result = await db.execute(
            select(TestAccess).where(
                TestAccess.test_id == test_id,
                TestAccess.group_id == group_id
            )
        )
        test_accesses = result.scalars().all()
        
        if not test_accesses:
            raise NotFoundException(f"Доступы к тесту {test_id} для группы {group_id} не найдены")
        
        # Удаляем все найденные записи
        for access in test_accesses:
            await db.delete(access)
        
        await db.commit()
        return {"detail": f"Удалено {len(test_accesses)} записей доступа к тесту"}
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при удалении доступов к тесту: {str(e)}")


async def get_test_users(db: AsyncSession, test_id: int):
    """Получить список пользователей, назначенных на тест"""
    try:
        result = await db.execute(
            select(TestAccess)
            .options(selectinload(TestAccess.user).selectinload(User.role))
            .options(selectinload(TestAccess.status))
            .where(TestAccess.test_id == test_id)
        )
        test_accesses = result.scalars().all()
        if not test_accesses:
            raise NotFoundException(f"Доступы к тесту {test_id} не найдены")
        users_with_access = []
        for access in test_accesses:
            if access.user:
                user_data = {
                    "user_id": access.user.id,
                    "email": access.user.email,
                    "name": access.user.name,
                    "role_id": access.user.role_id,
                    "role": {
                        "name": access.user.role.name if access.user.role else None,
                        "code": access.user.role.code if access.user.role else None
                    },
                    "access_id": access.id,
                    "group_id": access.group_id,
                    "start_date": access.start_date,
                    "end_date": access.end_date,
                    "status_id": access.status_id,
                    "status_name": access.status.name if access.status else None
                }
                users_with_access.append(user_data)
        return users_with_access
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении списка пользователей: {str(e)}")


async def get_test_groups(db: AsyncSession, test_id: int):
    """Получить список групп, назначенных на тест"""
    try:
        # Получаем уникальные group_id из записей доступа
        result = await db.execute(
            select(TestAccess.group_id)
            .where(TestAccess.test_id == test_id)
            .where(TestAccess.group_id.isnot(None))
            .distinct()
        )
        group_ids = [row[0] for row in result.all()]
        
        if not group_ids:
            raise NotFoundException(f"Группы с доступом к тесту {test_id} не найдены")
        
        # Для каждой группы получаем детальную информацию
        groups_with_access = []
        for group_id in group_ids:
            # Получаем информацию о группе
            group_result = await db.execute(
                select(UserGroup)
                .where(UserGroup.id == group_id)
            )
            group = group_result.scalar_one_or_none()
            
            if group:
                # Получаем количество пользователей в группе с доступом к тесту
                users_count_result = await db.execute(
                    select(func.count())
                    .select_from(TestAccess)
                    .where(
                        TestAccess.test_id == test_id,
                        TestAccess.group_id == group_id
                    )
                )
                users_count = users_count_result.scalar_one()
                
                group_data = {
                    "group_id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "users_count": users_count,
                    "created_at": group.created_at
                }
                groups_with_access.append(group_data)
        
        return groups_with_access
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении списка групп: {str(e)}")


async def update_test_access_status_by_user(db: AsyncSession, test_id: int, user_id: int, status_id: int):
    try:
        test_access = await get_test_access(db, test_id, user_id)
        if not test_access:
            raise NotFoundException(f"Доступ к тесту {test_id} для пользователя {user_id} не найден")
        status_result = await db.execute(
            select(TestAccessStatus).where(TestAccessStatus.id == status_id)
        )
        status = status_result.scalar_one_or_none()
        if not status:
            raise NotFoundException(f"Статус с ID {status_id} не найден")
        test_access.status_id = status_id
        await db.commit()
        await db.refresh(test_access)
        return test_access
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при обновлении статуса доступа: {str(e)}")
