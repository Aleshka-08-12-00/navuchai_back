from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import secrets

from app.models.course_access import CourseAccess
from app.models.user_group_member import UserGroupMember
from app.models.test_status import TestStatus
from app.models.course import Course, TestAccessEnum
from app.schemas.course_access import CourseAccessCreate
from app.exceptions import DatabaseException, NotFoundException

OPAQUE_TOKEN_NUM_BYTES = 16


def _generate_access_code() -> str:
    return secrets.token_urlsafe(OPAQUE_TOKEN_NUM_BYTES)


async def create_course_access(db: AsyncSession, access_data: CourseAccessCreate) -> CourseAccess:
    try:
        course = await db.scalar(select(Course).where(Course.id == access_data.course_id))
        if not course:
            raise NotFoundException(f"Курс с ID {access_data.course_id} не найден")

        data = access_data.model_dump(exclude_none=True)
        data.pop('access_code', None)
        db_access = CourseAccess(**data)

        if access_data.user_id:
            db_access.access_code = _generate_access_code()

        db.add(db_access)
        await db.commit()
        await db.refresh(db_access)
        return db_access
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при создании доступа к курсу: {str(e)}")


async def create_group_course_access(
    db: AsyncSession,
    course_id: int,
    group_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    status_id: int | None = None
) -> list[CourseAccess]:
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
            payload = CourseAccessCreate(
                course_id=course_id,
                user_id=member.user_id,
                group_id=group_id,
                start_date=start_date,
                end_date=end_date,
                status_id=status_id
            )
            created_access = await create_course_access(db, payload)
            created.append(created_access)
        return created
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании группового доступа к курсу")


async def get_course_access(db: AsyncSession, course_id: int, user_id: int) -> CourseAccess:
    try:
        query = select(CourseAccess).where(
            CourseAccess.course_id == course_id,
            CourseAccess.user_id == user_id
        ).options(selectinload(CourseAccess.status))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении доступа к курсу")


async def update_course_access(db: AsyncSession, course_id: int, access: str) -> Course:
    try:
        if access not in ['public', 'private']:
            raise ValueError("Значение access должно быть 'public' или 'private'")

        course = await db.scalar(select(Course).where(Course.id == course_id))
        if not course:
            raise NotFoundException(f"Курс с ID {course_id} не найден")

        await db.execute(update(Course).where(Course.id == course_id).values(access=access))
        await db.commit()
        return await db.scalar(select(Course).where(Course.id == course_id))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении доступа к курсу")
    except ValueError as e:
        raise DatabaseException(str(e))


async def get_course_access_code(db: AsyncSession, course_id: int, user_id: int) -> dict:
    course = await db.scalar(select(Course).where(Course.id == course_id))
    if not course:
        raise NotFoundException(f"Курс с id {course_id} не найден")

    if course.access == TestAccessEnum.PUBLIC:
        return {"code": course.id}

    access = await db.scalar(select(CourseAccess).where(
        CourseAccess.course_id == course_id,
        CourseAccess.user_id == user_id
    ))
    if not access:
        raise NotFoundException(f"Доступ к курсу {course_id} для пользователя {user_id} не найден")
    return {"access_code": access.access_code}
