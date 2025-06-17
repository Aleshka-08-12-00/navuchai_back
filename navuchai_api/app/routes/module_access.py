from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.dependencies import get_db
from app.crud import admin_moderator_required
from app.crud import module_access as crud
from app.models.user import User
from app.schemas.module_access import ModuleAccessCreate, ModuleAccessResponse
from app.schemas.module import ModuleWithLessons
from app.exceptions import DatabaseException, NotFoundException

router = APIRouter(prefix="/api/module-access", tags=["Module Access"])


@router.post("/user", response_model=ModuleAccessResponse)
async def create_user_module_access(
    module_access: ModuleAccessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> ModuleAccessResponse:
    try:
        if module_access.group_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Для предоставления доступа группе используйте endpoint /group"
            )

        existing = await crud.get_module_access(db, module_access.module_id, module_access.user_id)
        if existing:
            raise HTTPException(status_code=400, detail="У пользователя уже есть доступ к этому модулю")
        return await crud.create_module_access(db, module_access)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/group", response_model=List[ModuleAccessResponse])
async def create_group_module_access(
    module_id: int,
    group_id: int,
    start_date: datetime = None,
    end_date: datetime = None,
    status_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> List[ModuleAccessResponse]:
    try:
        return await crud.create_group_module_access(
            db=db,
            module_id=module_id,
            group_id=group_id,
            start_date=start_date,
            end_date=end_date,
            status_id=status_id
        )
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{module_id}/access", response_model=ModuleWithLessons)
async def update_module_access_type(
    module_id: int,
    access: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> ModuleWithLessons:
    try:
        return await crud.update_module_access(db, module_id, access)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{module_id}/code", response_model=dict)
async def get_module_access_code(
    module_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> dict:
    try:
        return await crud.get_module_access_code(db, module_id, current_user.id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))
