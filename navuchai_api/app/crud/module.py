from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app.models import Module
from app.exceptions import NotFoundException

async def create_module(db: AsyncSession, data):
    """
    Локальный импорт ModuleCreate разрывает цикл.
    """
    from app.schemas.module import ModuleCreate

    module = Module(**data.model_dump())
    db.add(module)
    await db.commit()
    await db.refresh(module)
    return module


async def get_module(db: AsyncSession, module_id: int):
    result = await db.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise NotFoundException("Модуль не найден")
    return module


async def update_module(db: AsyncSession, module_id: int, data):
    """
    Локально импортируем ModuleCreate (или ModuleUpdate) внутри функции.
    """
    from app.schemas.module import ModuleCreate  # или ModuleUpdate

    module = await get_module(db, module_id)
    module.title = data.title
    # Не заменяем module.order, чтобы он не стал None
    module.access = data.access

    await db.commit()
    await db.refresh(module)
    return module


async def delete_module(db: AsyncSession, module_id: int):
    module = await get_module(db, module_id)
    await db.delete(module)
    await db.commit()


async def get_modules_by_course(db: AsyncSession, course_id: int) -> list[Module]:
    stmt = (
        select(Module)
        .where(Module.course_id == course_id)
        .options(selectinload(Module.lessons))
        .order_by(Module.order)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_modules_with_lessons_by_course(db: AsyncSession, course_id: int) -> list[Module]:
    stmt = (
        select(Module)
        .options(selectinload(Module.lessons))
        .where(Module.course_id == course_id)
        .order_by(Module.order)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def create_module_for_course(db: AsyncSession, course_id: int, module_in):
    """
    Локально импортируем ModuleCreate, вычисляем order и создаём модуль.
    """
    from app.schemas.module import ModuleCreate

    # Узнаём текущий max order для этого курса
    stmt = select(func.max(Module.order)).where(Module.course_id == course_id)
    result = await db.execute(stmt)
    max_order = result.scalar()
    new_order = 1 if max_order is None else max_order + 1

    new = Module(
        title=module_in.title,
        order=new_order,
        course_id=course_id,
        access=module_in.access
    )
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return new
