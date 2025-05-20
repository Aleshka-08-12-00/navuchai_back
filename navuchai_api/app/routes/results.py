from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from app.crud import result as result_crud
from app.crud import authorized_required
from app.dependencies import get_db
from app.exceptions import NotFoundException, DatabaseException
from app.models import User, Result, UserAnswer
from app.schemas.result import ResultCreate, ResultResponse, UserAnswerResponse
from app.utils import convert_result


router = APIRouter(prefix="/api/results", tags=["Results"])


def convert_user_answer(answer: UserAnswer) -> UserAnswerResponse:
    """Преобразует модель UserAnswer в схему UserAnswerResponse"""
    return UserAnswerResponse(
        id=answer.id,
        result_id=answer.result_id,
        question_id=answer.question_id,
        user_id=answer.user_id,
        answer=answer.answer,
        created_at=answer.created_at,
        updated_at=answer.updated_at
    )


def convert_result(result: Result) -> ResultResponse:
    """Преобразует модель Result в схему ResultResponse"""
    return ResultResponse(
        id=result.id,
        user_id=result.user_id,
        test_id=result.test_id,
        score=result.score,
        completed_at=result.completed_at,
        created_at=result.created_at,
        updated_at=result.updated_at,
        answers=[convert_user_answer(answer) for answer in result.user_answers]
    )


@router.post("/", response_model=ResultResponse)
async def create_test_result(
    result: ResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        # Проверяем, что пользователь создает результат для себя
        if result.user_id != current_user.id:
            raise DatabaseException("Нельзя создать результат для другого пользователя")
        
        created_result = await result_crud.create_result(db, result)
        return convert_result(created_result)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при сохранении результата")


@router.get("/{result_id}", response_model=ResultResponse)
async def get_result_by_id(
    result_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        result = await result_crud.get_result(db, result_id)
        if not result:
            raise NotFoundException("Результат не найден")
        
        # Проверяем, что пользователь запрашивает свой результат
        if result.user_id != current_user.id:
            raise DatabaseException("Нет доступа к этому результату")
        
        return convert_result(result)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении результата")


@router.get("/user/{user_id}", response_model=List[ResultResponse])
async def get_user_results(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        # Проверяем, что пользователь запрашивает свои результаты
        if user_id != current_user.id:
            raise DatabaseException("Нет доступа к результатам другого пользователя")
            
        results = await result_crud.get_user_results(db, user_id)
        return [convert_result(result) for result in results]
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении результатов пользователя")


@router.get("/test/{test_id}", response_model=List[ResultResponse])
async def get_test_results(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        results = await result_crud.get_test_results(db, test_id)
        return [convert_result(result) for result in results]
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении результатов теста") 