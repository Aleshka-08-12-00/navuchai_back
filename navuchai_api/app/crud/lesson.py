from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app.models import Lesson, LessonProgress, Module, File
from app.schemas.lesson import LessonCreate
from app.exceptions import NotFoundException

async def create_lesson(db: AsyncSession, data: LessonCreate):
    """
    Создание урока без привязки к модулю.
    Если вы не используете этот метод напрямую, а только create_lesson_for_module,
    можно оставить его без вычисления order (либо удалить).
    """
    # Здесь предполагается, что data.model_dump() включает в себя module_id и все нужные поля.
    # Если хотите, чтобы метод create_lesson тоже вычислял order, добавьте логику по примеру ниже.
    if data.module_id is None:
        raise ValueError("module_id is required")
    lesson = Lesson(**data.model_dump())
    db.add(lesson)
    if data.file_ids:
        stmt_files = select(File).where(File.id.in_(data.file_ids))
        files_result = await db.execute(stmt_files)
        lesson.files = files_result.scalars().all()
    await db.commit()
    await db.refresh(lesson)
    return lesson


async def get_lesson(db: AsyncSession, lesson_id: int):
    result = await db.execute(
        select(Lesson)
        .options(selectinload(Lesson.image))
        .options(selectinload(Lesson.thumbnail))
        .options(selectinload(Lesson.files))
        .where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise NotFoundException("Урок не найден")
    return lesson


async def update_lesson(db: AsyncSession, lesson_id: int, data: LessonCreate):
    """
    При обновлении не трогаем поле order, а меняем только title и content.
    """
    lesson = await get_lesson(db, lesson_id)

    # Обновляем только те поля, которые действительно нужно менять.
    lesson.title = data.title
    lesson.description = data.description
    lesson.content = data.content
    lesson.video = data.video
    lesson.img_id = data.img_id
    lesson.thumbnail_id = data.thumbnail_id
    if data.file_ids:
        stmt_files = select(File).where(File.id.in_(data.file_ids))
        files_result = await db.execute(stmt_files)
        lesson.files = files_result.scalars().all()
    # НЕ переписываем lesson.order = data.order, иначе попадёт None и в БД будет ошибка.

    await db.commit()
    await db.refresh(lesson)
    return lesson


async def delete_lesson(db: AsyncSession, lesson_id: int):
    lesson = await get_lesson(db, lesson_id)
    await db.delete(lesson)
    await db.commit()


async def get_lessons_by_module(db: AsyncSession, module_id: int) -> list[Lesson]:
    stmt = (
        select(Lesson)
        .options(selectinload(Lesson.image))
        .options(selectinload(Lesson.thumbnail))
        .options(selectinload(Lesson.files))
        .where(Lesson.module_id == module_id)
        .order_by(Lesson.order)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_lesson_for_module(
    db: AsyncSession, module_id: int, lesson_in: LessonCreate
) -> Lesson:
    """
    При создании нового урока внутри модуля автоматически вычисляем поле order:
    берем максимальный order среди имеющихся уроков данного module_id и прибавляем 1.
    """
    # 1) Узнаём текущее максимальное значение order для этого module_id
    stmt = select(func.max(Lesson.order)).where(Lesson.module_id == module_id)
    result = await db.execute(stmt)
    max_order = result.scalar()  # либо число, либо None, если уроков ещё нет

    new_order = 1 if max_order is None else max_order + 1

    # 2) Создаём новый урок, передавая title, content и вычисленный order
    new = Lesson(
        title=lesson_in.title,
        description=lesson_in.description,
        content=lesson_in.content,
        video=lesson_in.video,
        img_id=lesson_in.img_id,
        thumbnail_id=lesson_in.thumbnail_id,
        order=new_order,
        module_id=module_id
    )
    db.add(new)
    if lesson_in.file_ids:
        stmt_files = select(File).where(File.id.in_(lesson_in.file_ids))
        files_res = await db.execute(stmt_files)
        new.files = files_res.scalars().all()
    await db.commit()
    await db.refresh(new)
    return new


async def complete_lesson(db: AsyncSession, lesson_id: int, user_id: int):
    existing = await db.execute(
        select(LessonProgress).where(
            LessonProgress.lesson_id == lesson_id,
            LessonProgress.user_id == user_id
        )
    )
    if existing.scalar_one_or_none():
        return
    progress = LessonProgress(lesson_id=lesson_id, user_id=user_id)
    db.add(progress)
    await db.commit()


async def get_module_progress(db: AsyncSession, module_id: int, user_id: int) -> float:
    total_res = await db.execute(select(func.count()).select_from(Lesson).where(Lesson.module_id == module_id))
    total = total_res.scalar() or 0
    if total == 0:
        return 0.0
    completed_res = await db.execute(
        select(func.count())
        .select_from(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .where(Lesson.module_id == module_id, LessonProgress.user_id == user_id)
    )
    completed = completed_res.scalar() or 0
    return round(completed / total * 100, 2)


async def get_course_progress(db: AsyncSession, course_id: int, user_id: int) -> float:
    total_res = await db.execute(
        select(func.count())
        .select_from(Lesson)
        .join(Module, Lesson.module_id == Module.id)
        .where(Module.course_id == course_id)
    )
    total = total_res.scalar() or 0
    if total == 0:
        return 0.0
    completed_res = await db.execute(
        select(func.count())
        .select_from(LessonProgress)
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .where(Module.course_id == course_id, LessonProgress.user_id == user_id)
    )
    completed = completed_res.scalar() or 0
    return round(completed / total * 100, 2)
