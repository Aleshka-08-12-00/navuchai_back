from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.crud.user import get_users, get_user, update_user, delete_user
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    return await get_users(db)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_id(user_id: int, update_data: UserUpdate, db: AsyncSession = Depends(get_db)):
    updated = await update_user(db, user_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted
