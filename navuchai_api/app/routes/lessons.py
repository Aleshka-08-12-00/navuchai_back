from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.crud import (
    create_lesson,
    get_lesson,
    update_lesson,
    delete_lesson,
    admin_moderator_required,
    complete_lesson,
    user_enrolled,
)
from app.crud import authorized_required, get_current_user
from app.schemas.lesson import LessonCreate, LessonResponse
from app.models import User

router = APIRouter(prefix="/api/lessons", tags=["Lessons"])


@router.post(
    "",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_moderator_required)],
)
async def create(data: LessonCreate, db: AsyncSession = Depends(get_db)):
    return await create_lesson(db, data)


@router.put(
    "/{lesson_id}",
    response_model=LessonResponse,
    dependencies=[Depends(admin_moderator_required)],
)
async def update(
    lesson_id: int, data: LessonCreate, db: AsyncSession = Depends(get_db)
):
    return await update_lesson(db, lesson_id, data)


@router.delete(
    "/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(admin_moderator_required)],
)
async def remove(lesson_id: int, db: AsyncSession = Depends(get_db)):
    await delete_lesson(db, lesson_id)


@router.get(
    "/{lesson_id}",
    response_model=LessonResponse,
    dependencies=[Depends(authorized_required)],
)
async def read(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lesson = await get_lesson(db, lesson_id)
    if user.role.code not in ["admin", "moderator"]:
        module = lesson.module
        if module and not await user_enrolled(db, module.course_id, user.id):
            raise HTTPException(status_code=403, detail="Нет доступа к уроку")
    await complete_lesson(db, lesson_id, user.id)
    setattr(lesson, "completed", True)
    return lesson


@router.post("/{lesson_id}/complete", dependencies=[Depends(authorized_required)])
async def mark_completed(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lesson = await get_lesson(db, lesson_id)
    if not lesson:
        return
    if user.role.code not in ["admin", "moderator"]:
        module = lesson.module
        if module and not await user_enrolled(db, module.course_id, user.id):
            raise HTTPException(status_code=403, detail="Нет доступа к уроку")
    await complete_lesson(db, lesson_id, user.id)
    return {"detail": "completed"}
