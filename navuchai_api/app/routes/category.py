from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import category as category_crud
from app.dependencies import get_db
from app.models import User
from app.crud.user_auth import get_current_user
from app.crud import admin_teacher_required
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryInDB

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.post("/", response_model=CategoryInDB)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
):
    return await category_crud.create_category(db=db, category=category)

@router.get("/{category_id}", response_model=CategoryInDB)
async def read_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
):
    return await category_crud.get_category(db=db, category_id=category_id)

@router.get("/", response_model=list[CategoryInDB])
async def read_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
):
    return await category_crud.get_categories(db=db)

@router.put("/{category_id}", response_model=CategoryInDB)
async def update_category(
    category_id: int,
    category: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
):
    return await category_crud.update_category(db=db, category_id=category_id, category=category)

@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
):
    await category_crud.delete_category(db=db, category_id=category_id)
    return {"message": "Категория успешно удалена"} 