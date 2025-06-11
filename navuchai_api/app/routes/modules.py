from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.crud import create_module, get_module, update_module, delete_module, admin_moderator_required, get_lessons_by_module, create_lesson_for_module
from app.schemas.module import ModuleCreate, ModuleWithLessons
from app.schemas.lesson import LessonResponse, LessonCreate
from app.exceptions import NotFoundException



router = APIRouter(prefix="/api/modules", tags=["Modules"], dependencies=[Depends(admin_moderator_required)])

@router.post("/", response_model=ModuleWithLessons, status_code=status.HTTP_201_CREATED)
async def create(data: ModuleCreate, db: AsyncSession = Depends(get_db)):
    return await create_module(db, data)

@router.put("/{module_id}", response_model=ModuleWithLessons)
async def update(module_id: int, data: ModuleCreate, db: AsyncSession = Depends(get_db)):
    return await update_module(db, module_id, data)

@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove(module_id: int, db: AsyncSession = Depends(get_db)):
    await delete_module(db, module_id)

@router.get(
    "/{module_id}/lessons",
    response_model=list[LessonResponse],
)
async def read_lessons(module_id: int, db: AsyncSession = Depends(get_db)):
    lessons = await get_lessons_by_module(db, module_id)
    if not lessons:
        raise HTTPException(status_code=404, detail="Lessons not found")
    return lessons

@router.post("/{module_id}/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson_route(module_id: int, data: LessonCreate, db: AsyncSession = Depends(get_db)):
    return await create_lesson_for_module(db, module_id, data)
