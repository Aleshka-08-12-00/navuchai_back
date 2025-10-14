from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.orm import selectinload
from app.models import CourseEnrollment, Course
from app.utils.activity_logger import log_user_activity
from app.utils.calendar_events import create_simple_event
from app.exceptions import NotFoundException

async def enroll_user(db: AsyncSession, course_id: int, user_id: int):
    existing = await db.execute(select(CourseEnrollment).where(and_(CourseEnrollment.course_id == course_id,
                                                                   CourseEnrollment.user_id == user_id)))
    if existing.scalar_one_or_none():
        return
    enroll = CourseEnrollment(course_id=course_id, user_id=user_id)
    db.add(enroll)
    await db.commit()
    await db.refresh(enroll)
    try:
        # Получаем информацию о курсе для контекста
        course_result = await db.execute(
            select(Course).where(Course.id == course_id)
        )
        course = course_result.scalar_one_or_none()
        
        context = {
            "course_id": course_id,
            "course_title": course.title if course else None,
            "enrolled_at": enroll.enrolled_at.isoformat() if enroll.enrolled_at else None
        }
        await log_user_activity(db, user_id=user_id, action="course_enrolled", context=context)

        # Календарь: событие назначения на курс
        try:
            await create_simple_event(
                db,
                user_id=user_id,
                title=(course.title if course else f"Курс #{course_id}"),
                type='task',
                starts_at=enroll.enrolled_at or datetime.utcnow(),
                ends_at=enroll.enrolled_at or datetime.utcnow(),
                link=None,
                created_by_user_id=None,
            )
        except Exception:
            pass
    except Exception:
        pass

async def unenroll_user(db: AsyncSession, course_id: int, user_id: int):
    result = await db.execute(select(CourseEnrollment).where(and_(CourseEnrollment.course_id == course_id,
                                                                  CourseEnrollment.user_id == user_id)))
    enroll = result.scalar_one_or_none()
    if not enroll:
        raise NotFoundException("Запись не найдена")
    
    # Сохраняем информацию о курсе и дате отчисления перед удалением
    course_result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = course_result.scalar_one_or_none()
    enrolled_at = enroll.enrolled_at.isoformat() if enroll.enrolled_at else None
    
    await db.delete(enroll)
    await db.commit()
    try:
        context = {
            "course_id": course_id,
            "course_title": course.title if course else None,
            "enrolled_at": enrolled_at,
            "unenrolled_at": enroll.updated_at.isoformat() if hasattr(enroll, 'updated_at') and enroll.updated_at else None
        }
        await log_user_activity(db, user_id=user_id, action="course_unenrolled", context=context)
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
