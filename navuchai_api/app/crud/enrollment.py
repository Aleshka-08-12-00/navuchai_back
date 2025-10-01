from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.models import CourseEnrollment
from app.utils.activity_logger import log_user_activity
from app.exceptions import NotFoundException

async def enroll_user(db: AsyncSession, course_id: int, user_id: int):
    existing = await db.execute(select(CourseEnrollment).where(and_(CourseEnrollment.course_id == course_id,
                                                                   CourseEnrollment.user_id == user_id)))
    if existing.scalar_one_or_none():
        return
    enroll = CourseEnrollment(course_id=course_id, user_id=user_id)
    db.add(enroll)
    await db.commit()
    try:
        await log_user_activity(db, user_id=user_id, action="course_enrolled", context={"course_id": course_id})
    except Exception:
        pass

async def unenroll_user(db: AsyncSession, course_id: int, user_id: int):
    result = await db.execute(select(CourseEnrollment).where(and_(CourseEnrollment.course_id == course_id,
                                                                  CourseEnrollment.user_id == user_id)))
    enroll = result.scalar_one_or_none()
    if not enroll:
        raise NotFoundException("Запись не найдена")
    await db.delete(enroll)
    await db.commit()
    try:
        await log_user_activity(db, user_id=user_id, action="course_unenrolled", context={"course_id": course_id})
    except Exception:
        pass

async def get_user_courses(db: AsyncSession, user_id: int):
    result = await db.execute(select(CourseEnrollment).where(CourseEnrollment.user_id == user_id))
    return result.scalars().all()


async def get_all_user_courses(db: AsyncSession):
    result = await db.execute(select(CourseEnrollment))
    return result.scalars().all()


async def user_enrolled(db: AsyncSession, course_id: int, user_id: int) -> bool:
    result = await db.execute(
        select(CourseEnrollment).where(
            and_(CourseEnrollment.course_id == course_id, CourseEnrollment.user_id == user_id)
        )
    )
    return result.scalar_one_or_none() is not None


async def get_users_courses_grouped(db: AsyncSession):
    """Получает все записи о зачислении с информацией о пользователях и курсах, сгруппированные по пользователям"""
    from sqlalchemy.orm import selectinload
    from app.models import User, Course
    
    # Получаем все записи о зачислении с загруженными связями
    result = await db.execute(
        select(CourseEnrollment)
        .options(selectinload(CourseEnrollment.user).selectinload(User.img))
        .options(selectinload(CourseEnrollment.user).selectinload(User.thumbnail))
        .options(selectinload(CourseEnrollment.course))
        .order_by(CourseEnrollment.user_id, CourseEnrollment.course_id)
    )
    
    enrollments = result.scalars().all()
    
    # Группируем по пользователям
    users_courses = {}
    
    for enrollment in enrollments:
        user_id = enrollment.user_id
        user_name = enrollment.user.name
        user_email = enrollment.user.email
        user_img = enrollment.user.img
        user_thumbnail = enrollment.user.thumbnail
        
        if user_id not in users_courses:
            users_courses[user_id] = {
                "user_id": user_id,
                "user_name": user_name,
                "user_email": user_email,
                "user_img": user_img,
                "user_thumbnail": user_thumbnail,
                "courses": []
            }
        
        # Добавляем информацию о курсе
        course_info = {
            "course_id": enrollment.course_id,
            "course_title": enrollment.course.title,
            "enrolled_at": enrollment.enrolled_at
        }
        
        users_courses[user_id]["courses"].append(course_info)
    
    # Преобразуем в список
    return list(users_courses.values())
