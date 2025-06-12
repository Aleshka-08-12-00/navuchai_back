from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models import Lesson
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
    lesson = Lesson(**data.model_dump())
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


async def get_lesson(db: AsyncSession, lesson_id: int):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
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
    lesson.content = data.content
    lesson.video = data.video
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
        content=lesson_in.content,
        video=lesson_in.video,
        order=new_order,
        module_id=module_id
    )
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return new
