from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from sqlalchemy import func
from app.models import Course, User, Module, Lesson, LessonProgress, CourseEnrollment
from app.schemas.course import CourseCreate
from .lesson import get_course_progress
from app.exceptions import NotFoundException, DatabaseException


async def get_courses(db: AsyncSession, user: User | None = None):
    result = await db.execute(
        select(Course, User.name)
        .join(User, Course.author_id == User.id)
        .options(selectinload(Course.image))
        .options(selectinload(Course.thumbnail))
    )

    courses = []

    # preload counts for all courses
    count_res = await db.execute(
        select(CourseEnrollment.course_id, func.count()).group_by(
            CourseEnrollment.course_id
        )
    )
    counts = dict(count_res.all())

    lessons_res = await db.execute(
        select(Module.course_id, func.count(Lesson.id))
        .select_from(Module)
        .join(Lesson, Lesson.module_id == Module.id, isouter=True)
        .group_by(Module.course_id)
    )
    lesson_counts = {cid: cnt for cid, cnt in lessons_res.all()}

    user_enrollments = {}
    if user:
        enroll_res = await db.execute(
            select(CourseEnrollment.course_id, CourseEnrollment.enrolled_at).where(
                CourseEnrollment.user_id == user.id
            )
        )
        user_enrollments = {cid: ts for cid, ts in enroll_res.all()}

    for c, name in result.all():
        enrolled_at = user_enrollments.get(c.id)
        enrolled = bool(enrolled_at)
        if user and user.role.code == "admin":
            enrolled = True
        enrolled_days = None
        if enrolled_at and user and user.role.code != "admin":
            enrolled_days = (datetime.now(timezone.utc) - enrolled_at).days

        progress = None
        done = False
        if user:
            if user.role.code == "admin":
                progress = 100
                done = True
            else:
                progress_float = await get_course_progress(db, c.id, user.id)
                progress = round(progress_float)
                done = progress == 100

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
                "students_count": counts.get(c.id, 0),
                "lessons_count": lesson_counts.get(c.id, 0),
                "enrolled": enrolled,
                "enrolled_days": enrolled_days,
                "done": done,
                "progress": progress,
            }
        )

    return courses


async def get_course_with_content(
    db: AsyncSession, course_id: int, user: User | None = None
) -> Course:
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

    # students count
    count_res = await db.execute(
        select(func.count())
        .select_from(CourseEnrollment)
        .where(CourseEnrollment.course_id == course_id)
    )
    course.students_count = count_res.scalar() or 0

    lesson_res = await db.execute(
        select(func.count())
        .select_from(Lesson)
        .join(Module, Lesson.module_id == Module.id)
        .where(Module.course_id == course.id)
    )
    course.lessons_count = lesson_res.scalar() or 0

    # lessons count already computed above

    # enrollment info
    course.enrolled = False
    course.enrolled_days = None
    course.done = False
    course.progress = None
    if user:
        if user.role.code == "admin":
            course.enrolled = True
            course.done = True
            course.progress = 100
        else:
            enr_res = await db.execute(
                select(CourseEnrollment.enrolled_at).where(
                    CourseEnrollment.course_id == course_id,
                    CourseEnrollment.user_id == user.id,
                )
            )
            enrolled_at = enr_res.scalar_one_or_none()
            if enrolled_at:
                course.enrolled = True
                course.enrolled_days = (datetime.now(timezone.utc) - enrolled_at).days
            progress = await get_course_progress(db, course_id, user.id)
            course.progress = round(progress)
            if course.progress == 100:
                course.done = True
    else:
        course.progress = None

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
    course.img_id = data.img_id
    course.thumbnail_id = data.thumbnail_id
    await db.commit()
    await db.refresh(course)
    return course


async def delete_course(db: AsyncSession, course_id: int):
    course = await get_course(db, course_id)
    await db.delete(course)
    await db.commit()


async def update_course_images(
    db: AsyncSession, course_id: int, img_id: int, thumbnail_id: int
) -> Course:
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

    course, lesson = row
    count_res = await db.execute(
        select(func.count())
        .select_from(CourseEnrollment)
        .where(CourseEnrollment.course_id == course.id)
    )
    course.students_count = count_res.scalar() or 0

    enr_res = await db.execute(
        select(CourseEnrollment.enrolled_at).where(
            CourseEnrollment.course_id == course.id,
            CourseEnrollment.user_id == user_id,
        )
    )
    enrolled_at = enr_res.scalar_one_or_none()
    course.enrolled = bool(enrolled_at)
    course.enrolled_days = None
    course.done = False
    course.progress = None
    if enrolled_at:
        course.enrolled_days = (datetime.now(timezone.utc) - enrolled_at).days
    progress = await get_course_progress(db, course.id, user_id)
    course.progress = round(progress)
    if course.progress == 100:
        course.done = True

    return course, lesson
