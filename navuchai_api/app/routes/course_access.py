from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.dependencies import get_db
from app.crud import admin_moderator_required
from app.crud import course_access as crud
from app.models.user import User
from app.schemas.course_access import CourseAccessCreate, CourseAccessResponse
from app.schemas.course import CourseResponse
from app.exceptions import DatabaseException, NotFoundException

router = APIRouter(prefix="/api/course-access", tags=["Course Access"])


@router.post("/user", response_model=CourseAccessResponse)
async def create_user_course_access(
    course_access: CourseAccessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> CourseAccessResponse:
    try:
        if course_access.group_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Для предоставления доступа группе используйте endpoint /group"
            )

        existing = await crud.get_course_access(db, course_access.course_id, course_access.user_id)
        if existing:
            raise HTTPException(status_code=400, detail="У пользователя уже есть доступ к этому курсу")
        return await crud.create_course_access(db, course_access)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/group", response_model=List[CourseAccessResponse])
async def create_group_course_access(
    course_id: int,
    group_id: int,
    start_date: datetime = None,
    end_date: datetime = None,
    status_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> List[CourseAccessResponse]:
    try:
        return await crud.create_group_course_access(
            db=db,
            course_id=course_id,
            group_id=group_id,
            start_date=start_date,
            end_date=end_date,
            status_id=status_id
        )
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{course_id}/access", response_model=CourseResponse)
async def update_course_access_type(
    course_id: int,
    access: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> CourseResponse:
    try:
        return await crud.update_course_access(db, course_id, access)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{course_id}/code", response_model=dict)
async def get_course_access_code(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> dict:
    try:
        return await crud.get_course_access_code(db, course_id, current_user.id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))
