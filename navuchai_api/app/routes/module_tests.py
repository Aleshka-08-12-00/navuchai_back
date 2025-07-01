from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.crud import (
    create_module_test,
    get_module_tests,
    get_module,
    get_module_progress,
    user_enrolled,
    admin_moderator_required,
    authorized_required,
    get_current_user,
)
from app.schemas.module_test import ModuleTestBase, ModuleTestCreate
from app.schemas.test import TestResponse
from app.models import User

router = APIRouter(prefix="/api/modules", tags=["Module Tests"])


@router.post("/{module_id}/tests/", response_model=ModuleTestBase, dependencies=[Depends(admin_moderator_required)])
async def create_module_test_route(module_id: int, data: ModuleTestCreate, db: AsyncSession = Depends(get_db)):
    data.module_id = module_id
    return await create_module_test(db, data)


@router.get("/{module_id}/tests/", response_model=list[TestResponse], dependencies=[Depends(authorized_required)])
async def list_module_tests_route(module_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    module = await get_module(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    if user.role.code not in ["admin", "moderator"] and not await user_enrolled(db, module.course_id, user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к модулю")
    progress = await get_module_progress(db, module_id, user.id)
    if user.role.code not in ["admin", "moderator"] and progress < 100:
        raise HTTPException(status_code=403, detail="Модуль не завершен")
    tests = await get_module_tests(db, module_id)
    return [t.test for t in tests]
