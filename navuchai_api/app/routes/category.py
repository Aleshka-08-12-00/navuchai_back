from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import category as category_crud
from app.dependencies import get_db
from app.models import User
from app.crud.user_auth import get_current_user
from app.crud import root_admin_moderator_required, authorized_required
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryInDB
from app.exceptions import DatabaseException, NotFoundException

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.post("/", response_model=CategoryInDB)
async def create_category(
        category: CategoryCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(root_admin_moderator_required)
):
    return await category_crud.create_category(db=db, category=category)


@router.get("/{category_id}/", response_model=CategoryInDB)
async def read_category(
        category_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    return await category_crud.get_category(db=db, category_id=category_id)


@router.get("/", response_model=list[CategoryInDB])
async def read_categories(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    return await category_crud.get_categories(db=db)


@router.get("/by-test-group/{test_group_id}/", response_model=list[CategoryInDB])
async def read_categories_by_test_group(
        test_group_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    """Получение категорий, которые используются в тестах конкретной группы тестов"""
    try:
        from app.crud.test_group import get_test_group_with_access_check
        
        # Проверяем доступ к группе тестов
        user_role_code = current_user.role.code if current_user.role else None
        await get_test_group_with_access_check(db, test_group_id, current_user.id, user_role_code)
        
        return await category_crud.get_categories_by_test_group(db=db, test_group_id=test_group_id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{category_id}/", response_model=CategoryInDB)
async def update_category(
        category_id: int,
        category: CategoryUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(root_admin_moderator_required)
):
    return await category_crud.update_category(db=db, category_id=category_id, category=category)


@router.delete("/{category_id}/")
async def delete_category(
        category_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(root_admin_moderator_required)
):
    await category_crud.delete_category(db=db, category_id=category_id)
    return {"message": "Категория успешно удалена"}
