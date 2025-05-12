from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.profile import get_user_profile, update_user_profile
from app.schemas.user import UserResponse, UserProfileUpdate
from app.dependencies import get_db
from app.models.user import User
from app.crud import authorized_required
from app.exceptions import NotFoundException, DatabaseException

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("/", response_model=UserResponse)
async def read_profile(
        current_user: User = Depends(authorized_required),
        db: AsyncSession = Depends(get_db)
):
    try:
        return await get_user_profile(db, current_user.id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/", response_model=UserResponse)
async def update_profile(
        profile: UserProfileUpdate,
        current_user: User = Depends(authorized_required),
        db: AsyncSession = Depends(get_db)
):
    try:
        return await update_user_profile(db, current_user.id, profile)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
