from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.dependencies import get_db
from app.crud import admin_moderator_required
from app.crud import lesson_access as crud
from app.models.user import User
from app.schemas.lesson_access import LessonAccessCreate, LessonAccessResponse
from app.schemas.lesson import LessonWithTests
from app.exceptions import DatabaseException, NotFoundException

router = APIRouter(prefix="/api/lesson-access", tags=["Lesson Access"])


@router.post("/user", response_model=LessonAccessResponse)
async def create_user_lesson_access(
    lesson_access: LessonAccessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> LessonAccessResponse:
    try:
        if lesson_access.group_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Для предоставления доступа группе используйте endpoint /group"
            )

        existing = await crud.get_lesson_access(db, lesson_access.lesson_id, lesson_access.user_id)
        if existing:
            raise HTTPException(status_code=400, detail="У пользователя уже есть доступ к этому уроку")
        return await crud.create_lesson_access(db, lesson_access)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/group", response_model=List[LessonAccessResponse])
async def create_group_lesson_access(
    lesson_id: int,
    group_id: int,
    start_date: datetime = None,
    end_date: datetime = None,
    status_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> List[LessonAccessResponse]:
    try:
        return await crud.create_group_lesson_access(
            db=db,
            lesson_id=lesson_id,
            group_id=group_id,
            start_date=start_date,
            end_date=end_date,
            status_id=status_id
        )
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{lesson_id}/access", response_model=LessonWithTests)
async def update_lesson_access_type(
    lesson_id: int,
    access: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> LessonWithTests:
    try:
        return await crud.update_lesson_access(db, lesson_id, access)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{lesson_id}/code", response_model=dict)
async def get_lesson_access_code(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
) -> dict:
    try:
        return await crud.get_lesson_access_code(db, lesson_id, current_user.id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))
