from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.dependencies import get_db
from app.crud import admin_teacher_required
from app.crud import test_access as crud
from app.models.user import User
from app.schemas.test_access import TestAccessCreate, TestAccessResponse
from app.schemas.test import TestResponse
from app.exceptions import DatabaseException, NotFoundException

router = APIRouter(prefix="/api/test-access", tags=["Test Access"])


@router.post("/user", response_model=TestAccessResponse)
async def create_user_test_access(
    test_access: TestAccessCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
) -> TestAccessResponse:
    try:
        if test_access.group_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Для предоставления доступа группе используйте endpoint /group"
            )
        
        # Проверяем, нет ли уже доступа у пользователя к этому тесту
        existing_access = await crud.get_test_access(db, test_access.test_id, test_access.user_id)
        if existing_access:
            raise HTTPException(
                status_code=400,
                detail="У пользователя уже есть доступ к этому тесту"
            )
        
        return await crud.create_test_access(db, test_access)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/group", response_model=List[TestAccessResponse])
async def create_group_test_access(
    test_id: int,
    group_id: int,
    start_date: datetime = None,
    end_date: datetime = None,
    status_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
) -> List[TestAccessResponse]:
    try:
        return await crud.create_group_test_access(
            db=db,
            test_id=test_id,
            group_id=group_id,
            start_date=start_date,
            end_date=end_date,
            status_id=status_id
        )
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{test_id}/access", response_model=TestResponse)
async def update_test_access_type(
    test_id: int,
    access: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
) -> TestResponse:
    """
    Изменение типа доступа к тесту (public/private)
    """
    try:
        return await crud.update_test_access(db, test_id, access)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{test_id}/code", response_model=dict)
async def get_test_access_code(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_teacher_required)
) -> dict:
    """
    Получение кода доступа к тесту:
    - Если тест публичный, возвращает code из таблицы tests
    - Если тест приватный, возвращает access_code из таблицы test_access
    """
    try:
        return await crud.get_test_access_code(db, test_id, current_user.id)
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e)) 