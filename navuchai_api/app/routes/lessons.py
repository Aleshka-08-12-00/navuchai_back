from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.crud import create_lesson, get_lesson, update_lesson, delete_lesson, admin_moderator_required
from app.schemas.lesson import LessonCreate, LessonResponse
router = APIRouter(prefix="/api/lessons", tags=["Lessons"], dependencies=[Depends(admin_moderator_required)])

@router.post("/", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create(data: LessonCreate, db: AsyncSession = Depends(get_db)):
    return await create_lesson(db, data)

@router.put("/{lesson_id}", response_model=LessonResponse)
async def update(lesson_id: int, data: LessonCreate, db: AsyncSession = Depends(get_db)):
    return await update_lesson(db, lesson_id, data)

@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove(lesson_id: int, db: AsyncSession = Depends(get_db)):
    await delete_lesson(db, lesson_id)
