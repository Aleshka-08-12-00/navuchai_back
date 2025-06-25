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
