from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import CourseRating


async def set_course_rating(db: AsyncSession, course_id: int, user_id: int, rating: int) -> CourseRating:
    result = await db.execute(
        select(CourseRating).where(CourseRating.course_id == course_id, CourseRating.user_id == user_id)
    )
    obj = result.scalar_one_or_none()
    if obj:
        obj.rating = rating
    else:
        obj = CourseRating(course_id=course_id, user_id=user_id, rating=rating)
        db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_course_avg_rating(db: AsyncSession, course_id: int) -> float:
    res = await db.execute(
        select(func.avg(CourseRating.rating)).where(CourseRating.course_id == course_id)
    )
    value = res.scalar()
    return float(value) if value is not None else 0.0
