from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.crud import get_users, get_user, update_user, delete_user, admin_moderator_required, admin_required, update_user_role
from app.dependencies import get_db
from app.exceptions import NotFoundException, DatabaseException
from app.schemas.user import UserResponse, UserUpdate, UserRoleUpdate

router = APIRouter(prefix="/api/users", tags=["Users"], dependencies=[Depends(admin_moderator_required)])


@router.get("/", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    return await get_users(db)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        user = await get_user(db, user_id)
        if not user:
            raise NotFoundException("Пользователь не найден")
        return user
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных пользователя")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_id(user_id: int, update_data: UserUpdate, db: AsyncSession = Depends(get_db)):
    try:
        updated = await update_user(db, user_id, update_data)
        if not updated:
            raise NotFoundException("Пользователь не найден")
        return updated
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении данных пользователя")


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        deleted = await delete_user(db, user_id)
        if not deleted:
            raise NotFoundException("Пользователь не найден")
        return deleted
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при удалении пользователя")


@router.put("/{user_id}/role", dependencies=[Depends(admin_required)])
async def change_user_role(
    user_id: int,
    update_role: UserRoleUpdate,  # <-- вот здесь
    db: AsyncSession = Depends(get_db),
):
    user = await update_user_role(db, user_id, update_role.role_code.value)
    return {
        "message": f"User role updated",
        "user_id": user.id,
        "new_role": update_role.role_code.value
    }
