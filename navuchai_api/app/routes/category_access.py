from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models import User
from app.crud.user_auth import get_current_user
from app.crud import root_admin_moderator_required
from app.schemas.category_access import CategoryAccessCreate, CategoryAccessUpdate, CategoryAccessInDB
from app.crud import category_access as crud
from app.exceptions import DatabaseException, NotFoundException


router = APIRouter(prefix="/api/category-access", tags=["CategoryAccess"])


@router.post("/", response_model=CategoryAccessInDB)
async def create(
    payload: CategoryAccessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(root_admin_moderator_required),
):
    try:
        return await crud.create_category_access(db, payload)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[CategoryAccessInDB])
async def list_accesses(
    category_id: int | None = Query(default=None),
    user_group_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(root_admin_moderator_required),
):
    try:
        return await crud.list_category_accesses(db, category_id, user_group_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{access_id}/", response_model=CategoryAccessInDB)
async def update(
    access_id: int,
    payload: CategoryAccessUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(root_admin_moderator_required),
):
    try:
        return await crud.update_category_access(db, access_id, payload)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{access_id}/")
async def delete(
    access_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(root_admin_moderator_required),
):
    try:
        await crud.delete_category_access(db, access_id)
        return {"message": "Доступ удалён"}
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


