from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import ModuleTest
from app.schemas.module_test import ModuleTestCreate


async def create_module_test(db: AsyncSession, data: ModuleTestCreate) -> ModuleTest:
    module_test = ModuleTest(**data.model_dump())
    db.add(module_test)
    await db.commit()
    await db.refresh(module_test)
    return module_test


async def get_module_tests(db: AsyncSession, module_id: int) -> list[ModuleTest]:
    result = await db.execute(
        select(ModuleTest).where(ModuleTest.module_id == module_id).options(selectinload(ModuleTest.test))
    )
    return result.scalars().all()
