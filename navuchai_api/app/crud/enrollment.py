from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.models import CourseEnrollment
from app.exceptions import NotFoundException

async def enroll_user(db: AsyncSession, course_id: int, user_id: int):
    existing = await db.execute(select(CourseEnrollment).where(and_(CourseEnrollment.course_id == course_id,
                                                                   CourseEnrollment.user_id == user_id)))
    if existing.scalar_one_or_none():
        return
    enroll = CourseEnrollment(course_id=course_id, user_id=user_id)
    db.add(enroll)
    await db.commit()

async def unenroll_user(db: AsyncSession, course_id: int, user_id: int):
    result = await db.execute(select(CourseEnrollment).where(and_(CourseEnrollment.course_id == course_id,
                                                                  CourseEnrollment.user_id == user_id)))
    enroll = result.scalar_one_or_none()
    if not enroll:
        raise NotFoundException("Запись не найдена")
    await db.delete(enroll)
    await db.commit()

async def get_user_courses(db: AsyncSession, user_id: int):
    result = await db.execute(select(CourseEnrollment).where(CourseEnrollment.user_id == user_id))
    return result.scalars().all()


async def user_enrolled(db: AsyncSession, course_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(CourseEnrollment).where(
            and_(CourseEnrollment.course_id == course_id, CourseEnrollment.user_id == user_id)
        )
    )
    return result.scalar_one_or_none() is not None
