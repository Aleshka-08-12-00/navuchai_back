from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import CourseTest
from app.schemas.course_test import CourseTestCreate


async def create_course_test(db: AsyncSession, data: CourseTestCreate) -> CourseTest:
    course_test = CourseTest(**data.model_dump())
    db.add(course_test)
    await db.commit()
    await db.refresh(course_test)
    return course_test


async def get_course_tests(db: AsyncSession, course_id: int) -> list[CourseTest]:
    result = await db.execute(
        select(CourseTest).where(CourseTest.course_id == course_id).options(selectinload(CourseTest.test))
    )
    return result.scalars().all()


async def get_course_test(db: AsyncSession, course_id: int, test_id: int) -> CourseTest | None:
    result = await db.execute(
        select(CourseTest)
        .where(CourseTest.course_id == course_id, CourseTest.test_id == test_id)
        .options(selectinload(CourseTest.test))
    )
    return result.scalar_one_or_none()


async def delete_course_test(db: AsyncSession, course_id: int, test_id: int) -> CourseTest | None:
    course_test = await get_course_test(db, course_id, test_id)
    if not course_test:
        return None
    await db.delete(course_test)
    await db.commit()
    return course_test
