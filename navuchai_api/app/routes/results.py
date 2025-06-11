from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO

from app.crud import result as result_crud
from app.crud import authorized_required
from app.dependencies import get_db
from app.exceptions import NotFoundException, DatabaseException, ForbiddenException
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


@router.get("/excel")
async def export_results_excel(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        results = await result_crud.get_all_results(db)
        data = []
        for r in results:
            # result.result может быть None, если старые записи
            result_json = r.result or {}
            checked_answers = result_json.get("checked_answers", [])
            percentage = result_json.get("percentage", None)
            for ans in checked_answers:
                data.append({
                    "attempt_id": r.id,
                    "test_id": r.test_id,
                    "user_id": r.user_id,
                    "score": r.score,
                    "percentage": percentage,
                    "completed_at": r.completed_at,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                    "question_id": ans.get("question_id"),
                    "question_text": ans.get("question_text"),
                    "question_type": ans.get("question_type"),
                    "user_answer": str(ans.get("check_details", {}).get("user_answer")),
                    "correct_answer": str(ans.get("check_details", {}).get("correct_answer")),
                    "is_correct": ans.get("is_correct"),
                    "score_for_question": ans.get("score"),
                    "max_score": ans.get("max_score"),
                })
        df = pd.DataFrame(data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=results.xlsx"}
        )
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при экспорте результатов в Excel")


@router.post("/", response_model=ResultResponse)
async def create_test_result(
        result: ResultCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        # Проверяем, что пользователь создает результат для себя
        if result.user_id != current_user.id:
            raise ForbiddenException("Нельзя создать результат для другого пользователя")

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
        # Если не admin — проверяем, что пользователь запрашивает свой результат
        if current_user.role.code != "admin" and result.user_id != current_user.id:
            raise ForbiddenException("Нет доступа к этому результату")
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
        # Если не admin — проверяем, что пользователь запрашивает свои результаты
        if current_user.role.code != "admin" and user_id != current_user.id:
            raise ForbiddenException("Нет доступа к результатам другого пользователя")
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


@router.get("/", response_model=List[ResultResponse])
async def get_all_results(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        if current_user.role.code == "admin":
            results = await result_crud.get_all_results(db)
        else:
            results = await result_crud.get_user_results(db, current_user.id)
        return [convert_result(result) for result in results]
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка результатов")
