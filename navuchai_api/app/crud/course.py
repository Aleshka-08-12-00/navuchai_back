from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from app.models import Course, User, Module, Lesson, LessonProgress, CourseEnrollment
from app.schemas.course import CourseCreate
from app.exceptions import NotFoundException, DatabaseException
from app.models import CourseEnrollment
from sqlalchemy import and_
from .lesson import get_course_progress

async def get_courses(db: AsyncSession, user_id: int | None = None):
    stmt = (
        select(Course, User.name)
        .join(User, Course.author_id == User.id)
        .options(selectinload(Course.image))
        .options(selectinload(Course.thumbnail))
    )
    if user_id is not None:
        stmt = (
            stmt.outerjoin(
                CourseEnrollment,
                and_(
                    CourseEnrollment.course_id == Course.id,
                    CourseEnrollment.user_id == user_id,
                ),
            )
            .add_columns(CourseEnrollment.id)
        )
    result = await db.execute(stmt)
    courses = []
    for row in result.all():
        if user_id is not None:
            c, name, enroll_id = row
            enrolled = enroll_id is not None
            progress = await get_course_progress(db, c.id, user_id)
        else:
            c, name = row
            enrolled = None
            progress = None
        courses.append(
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "author_id": c.author_id,
                "author_name": name,
                "created_at": c.created_at,
                "img_id": c.img_id,
                "thumbnail_id": c.thumbnail_id,
                "image": c.image,
                "thumbnail": c.thumbnail,
                "enrolled": enrolled,
                "progress": progress,
                "done": progress == 100 if progress is not None else None,
            }
        )
    return courses

async def get_course_with_content(db: AsyncSession, course_id: int) -> Course:
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.image),
            selectinload(Course.thumbnail),
            selectinload(Course.modules).selectinload(Module.lessons),
        )
        .where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundException("Курс не найден")
    return course


async def get_course(db: AsyncSession, course_id: int):
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.image))
        .options(selectinload(Course.thumbnail))
        .where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundException("Курс не найден")
    return course

async def create_course(db: AsyncSession, data: CourseCreate, author_id: int):
    new_course = Course(
        title=data.title,
        description=data.description,
        author_id=author_id,
        img_id=data.img_id,
        thumbnail_id=data.thumbnail_id,
    )
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    return new_course

async def update_course(db: AsyncSession, course_id: int, data: CourseCreate):
    course = await get_course(db, course_id)
    course.title = data.title
    course.description = data.description
    if data.img_id is not None:
        course.img_id = data.img_id
    if data.thumbnail_id is not None:
        course.thumbnail_id = data.thumbnail_id
    await db.commit()
    await db.refresh(course)
    return course

async def delete_course(db: AsyncSession, course_id: int):
    course = await get_course(db, course_id)
    await db.delete(course)
    await db.commit()

async def update_course_images(db: AsyncSession, course_id: int, img_id: int, thumbnail_id: int) -> Course:
    """Обновить изображения курса."""
    course = await get_course(db, course_id)
    course.img_id = img_id
    course.thumbnail_id = thumbnail_id
    await db.commit()
    await db.refresh(course)
    return course


async def get_last_course_and_lesson(db: AsyncSession, user_id: int):
    stmt = (
        select(Course, Lesson)
        .join(Module, Module.course_id == Course.id)
        .join(Lesson, Lesson.module_id == Module.id)
        .join(LessonProgress, LessonProgress.lesson_id == Lesson.id)
        .where(LessonProgress.user_id == user_id)
        .order_by(LessonProgress.completed_at.desc())
        .options(selectinload(Course.image))
        .options(selectinload(Course.thumbnail))
        .options(selectinload(Lesson.image))
        .options(selectinload(Lesson.thumbnail))
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        return None, None
    return row


async def get_course_lessons_count(db: AsyncSession, course_id: int) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Lesson)
        .join(Module, Lesson.module_id == Module.id)
        .where(Module.course_id == course_id)
    )
    return result.scalar() or 0


async def get_course_students_count(db: AsyncSession, course_id: int) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(CourseEnrollment)
        .where(CourseEnrollment.course_id == course_id)
    )
    return result.scalar() or 0
