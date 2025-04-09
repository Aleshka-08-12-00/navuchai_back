from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies import get_db
from app.crud import get_tests, get_test, create_test, delete_test
from app.schemas import TestCreate, TestResponse, TestWithDetails
from app.exceptions import NotFoundException, DatabaseException

router = APIRouter(prefix="/api/tests", tags=["Tests"])


# Получение списка всех тестов
@router.get("/", response_model=list[TestWithDetails])
async def list_tests(db: AsyncSession = Depends(get_db)):
    return await get_tests(db)


# Получение конкретного теста по ID
@router.get("/{test_id}", response_model=TestResponse)
async def get_test_by_id(test_id: int, db: AsyncSession = Depends(get_db)):
    test = await get_test(db, test_id)
    if not test:
        raise NotFoundException("Test not found")
    return test


# Создание нового теста
@router.post("/", response_model=TestResponse)
async def create_new_test(test: TestCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await create_test(db, test)
    except SQLAlchemyError:
        raise DatabaseException("Error creating test")


# Удаление теста по ID
@router.delete("/{test_id}", response_model=TestResponse)
async def delete_test_by_id(test_id: int, db: AsyncSession = Depends(get_db)):
    try:
        test = await delete_test(db, test_id)
        if not test:
            raise NotFoundException("Test not found")
        return test
    except SQLAlchemyError:
        raise DatabaseException("Error deleting test")
