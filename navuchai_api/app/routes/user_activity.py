from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.crud.user_activity import create_user_activity, get_user_activities
from app.schemas.user_activity import UserActivityCreate, UserActivityRead
from app.crud import authorized_required
from app.models import User


router = APIRouter(prefix="/api/user-activities", tags=["UserActivities"])


@router.get("/{user_id}/", response_model=List[UserActivityRead])
async def list_user_activities(
    user_id: int,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    action: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required),
):
    return await get_user_activities(db, user_id=user_id, limit=limit, offset=offset, action=action)


@router.post("/", response_model=UserActivityRead)
async def add_user_activity(
    payload: UserActivityCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required),
):
    data = payload.copy()
    if data.ip is None:
        data.ip = request.client.host if request.client else None
    if data.user_agent is None:
        data.user_agent = request.headers.get("user-agent")
    return await create_user_activity(db, data)


