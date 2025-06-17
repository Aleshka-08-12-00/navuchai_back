from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import secrets

from app.models.lesson_access import LessonAccess
from app.models.user_group_member import UserGroupMember
from app.models.test_status import TestStatus
from app.models.lesson import Lesson, TestAccessEnum
from app.schemas.lesson_access import LessonAccessCreate
from app.exceptions import DatabaseException, NotFoundException

OPAQUE_TOKEN_NUM_BYTES = 16


def _generate_access_code() -> str:
    return secrets.token_urlsafe(OPAQUE_TOKEN_NUM_BYTES)


async def create_lesson_access(db: AsyncSession, access_data: LessonAccessCreate) -> LessonAccess:
    try:
        lesson = await db.scalar(select(Lesson).where(Lesson.id == access_data.lesson_id))
        if not lesson:
            raise NotFoundException(f"Урок с ID {access_data.lesson_id} не найден")

        data = access_data.model_dump(exclude_none=True)
        data.pop('access_code', None)
        db_access = LessonAccess(**data)

        if access_data.user_id:
            db_access.access_code = _generate_access_code()

        db.add(db_access)
        await db.commit()
        await db.refresh(db_access)
        return db_access
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при создании доступа к уроку: {str(e)}")


async def create_group_lesson_access(
    db: AsyncSession,
    lesson_id: int,
    group_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    status_id: int | None = None
) -> list[LessonAccess]:
    try:
        if status_id:
            status = await db.scalar(select(TestStatus).where(TestStatus.id == status_id))
            if not status:
                raise NotFoundException(f"Статус с ID {status_id} не найден")

        result = await db.execute(select(UserGroupMember).where(UserGroupMember.group_id == group_id))
        members = result.scalars().all()
        if not members:
            raise NotFoundException(f"В группе с ID {group_id} нет пользователей")

        created = []
        for member in members:
            payload = LessonAccessCreate(
                lesson_id=lesson_id,
                user_id=member.user_id,
                group_id=group_id,
                start_date=start_date,
                end_date=end_date,
                status_id=status_id
            )
            created_access = await create_lesson_access(db, payload)
            created.append(created_access)
        return created
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании группового доступа к уроку")


async def get_lesson_access(db: AsyncSession, lesson_id: int, user_id: int) -> LessonAccess:
    try:
        query = select(LessonAccess).where(
            LessonAccess.lesson_id == lesson_id,
            LessonAccess.user_id == user_id
        ).options(selectinload(LessonAccess.status))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении доступа к уроку")


async def update_lesson_access(db: AsyncSession, lesson_id: int, access: str) -> Lesson:
    try:
        if access not in ['public', 'private']:
            raise ValueError("Значение access должно быть 'public' или 'private'")

        lesson = await db.scalar(select(Lesson).where(Lesson.id == lesson_id))
        if not lesson:
            raise NotFoundException(f"Урок с ID {lesson_id} не найден")

        await db.execute(update(Lesson).where(Lesson.id == lesson_id).values(access=access))
        await db.commit()
        return await db.scalar(select(Lesson).where(Lesson.id == lesson_id))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении доступа к уроку")
    except ValueError as e:
        raise DatabaseException(str(e))


async def get_lesson_access_code(db: AsyncSession, lesson_id: int, user_id: int) -> dict:
    lesson = await db.scalar(select(Lesson).where(Lesson.id == lesson_id))
    if not lesson:
        raise NotFoundException(f"Урок с id {lesson_id} не найден")

    if lesson.access == TestAccessEnum.PUBLIC:
        return {"code": lesson.id}

    access = await db.scalar(select(LessonAccess).where(
        LessonAccess.lesson_id == lesson_id,
        LessonAccess.user_id == user_id
    ))
    if not access:
        raise NotFoundException(f"Доступ к уроку {lesson_id} для пользователя {user_id} не найден")
    return {"access_code": access.access_code}
