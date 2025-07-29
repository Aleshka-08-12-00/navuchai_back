from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.crud import (
    grant_category_access,
    revoke_category_access,
    get_user_categories,
    authorized_required,
    get_current_user,
    admin_moderator_required,
)
from app.models import User

router = APIRouter(prefix="/api/categories", tags=["CategoryAccess"])


@router.post("/{category_id}/access/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(authorized_required)])
async def grant_access(category_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await grant_category_access(db, category_id, user.id)


@router.post("/{category_id}/access/{user_id}/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(admin_moderator_required)])
async def grant_access_admin(category_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    await grant_category_access(db, category_id, user_id)


@router.delete("/{category_id}/access/{user_id}/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(admin_moderator_required)])
async def revoke_access(category_id: int, user_id: int, db: AsyncSession = Depends(get_db)):
    await revoke_category_access(db, category_id, user_id)


@router.get("/users/{user_id}/categories/")
async def user_categories(user_id: int, db: AsyncSession = Depends(get_db)):
    return await get_user_categories(db, user_id)
