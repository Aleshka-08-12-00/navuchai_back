from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models import CourseRating


async def set_course_rating(db: AsyncSession, course_id: int, user_id: int, rating: int) -> CourseRating:
    result = await db.execute(
        select(CourseRating).where(
            CourseRating.course_id == course_id,
            CourseRating.user_id == user_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        await db.delete(existing)
        await db.commit()
    new_rating = CourseRating(course_id=course_id, user_id=user_id, rating=rating)
    db.add(new_rating)
    await db.commit()
    await db.refresh(new_rating)
    return new_rating


async def get_average_course_rating(db: AsyncSession, course_id: int) -> float:
    result = await db.execute(
        select(func.avg(CourseRating.rating)).where(CourseRating.course_id == course_id)
    )
    avg = result.scalar()
    return float(avg) if avg is not None else 0.0
