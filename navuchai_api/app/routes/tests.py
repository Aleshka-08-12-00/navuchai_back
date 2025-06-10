from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    get_tests,
    get_test,
    create_test,
    delete_test,
    update_test,
    get_user_tests,
    admin_moderator_required,
    authorized_required
)
from app.dependencies import get_db
from app.exceptions import NotFoundException, DatabaseException
from app.models import User
from app.schemas.test import TestCreate, TestResponse, TestWithDetails, TestUpdate

router = APIRouter(prefix="/api/tests", tags=["Tests"])


@router.get("/", response_model=list[TestWithDetails])
async def get_all_tests(db: AsyncSession = Depends(get_db)): #, user: User = Depends(authorized_required)):
    try:
        return await get_tests(db)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка тестов")


@router.get("/my", response_model=list[TestWithDetails])
async def get_my_tests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        return await get_user_tests(db, current_user.id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка тестов пользователя")


@router.get("/{test_id}", response_model=TestWithDetails)
async def get_test_by_id(test_id: int, db: AsyncSession = Depends(get_db)): #, user: User = Depends(authorized_required)):
    try:
        test = await get_test(db, test_id)
        if not test:
            raise NotFoundException("Тест не найден")
        return test
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных теста")


@router.post("/", response_model=TestResponse)
async def create_new_test(test: TestCreate, db: AsyncSession = Depends(get_db), user: User = Depends(admin_moderator_required)):
    try:
        return await create_test(db, test)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании теста")


@router.put("/{test_id}", response_model=TestResponse)
async def update_test_by_id(test_id: int, test: TestUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(admin_moderator_required)):
    try:
        updated_test = await update_test(db, test_id, test)
        if not updated_test:
            raise NotFoundException("Тест не найден")
        return updated_test
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении теста")


@router.delete("/{test_id}", response_model=TestResponse)
async def delete_test_by_id(test_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(admin_moderator_required)):
    try:
        test = await delete_test(db, test_id)
        if not test:
            raise NotFoundException("Тест не найден")
        return test
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при удалении теста")
