from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from app.models import Course, User, Module, Lesson
from app.schemas.course import CourseCreate
from app.exceptions import NotFoundException, DatabaseException

async def get_courses(db: AsyncSession):
    result = await db.execute(
        select(Course, User.name)
        .join(User, Course.author_id == User.id)
        .options(selectinload(Course.image))
        .options(selectinload(Course.thumbnail))
    )
    return [
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
        }
        for c, name in result.all()
    ]

async def get_course_with_content(db, course_id: int) -> Course:
    stmt = (
        select(Course)
        .options(
            selectinload(Course.modules)
            .selectinload(Module.lessons)
            .selectinload(Lesson.image)
            .selectinload(Lesson.thumbnail)
        )
        .options(selectinload(Course.image))
        .options(selectinload(Course.thumbnail))
        .where(Course.id == course_id)
    )
    result = await db.execute(stmt)
    return result.scalars().first()

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

async def update_course_images(db: AsyncSession, course_id: int, img_id: int, thumbnail_id: int) -> Course:
    """Обновить изображения курса."""
    course = await get_course(db, course_id)
    course.img_id = img_id
    course.thumbnail_id = thumbnail_id
    await db.commit()
    await db.refresh(course)
    return course
