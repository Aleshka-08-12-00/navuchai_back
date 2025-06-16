from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.crud import question_type as crud
from app.dependencies import get_db
from app.exceptions import DatabaseException
from app.schemas.question_type import QuestionTypeCreate, QuestionTypeUpdate, QuestionTypeResponse
from app.crud import admin_moderator_required
from app.models import User

router = APIRouter(prefix="/api/question-types", tags=["Question Types"])


@router.get("/", response_model=list[QuestionTypeResponse])
async def list_question_types(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_moderator_required)
):
    try:
        return await crud.get_question_types(db)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка типов вопросов")


@router.get("/{type_id}", response_model=QuestionTypeResponse)
async def get_question_type(
    type_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(admin_moderator_required)
):
    try:
        return await crud.get_question_type(db, type_id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении типа вопроса")


@router.post("/", response_model=QuestionTypeResponse, dependencies=[Depends(admin_moderator_required)])
async def create_question_type(question_type: QuestionTypeCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await crud.create_question_type(db, question_type)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании типа вопроса")


@router.put("/{type_id}", response_model=QuestionTypeResponse, dependencies=[Depends(admin_moderator_required)])
async def update_question_type(type_id: int, question_type: QuestionTypeUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await crud.update_question_type(db, type_id, question_type)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении типа вопроса")


@router.delete("/{type_id}", response_model=QuestionTypeResponse, dependencies=[Depends(admin_moderator_required)])
async def delete_question_type(type_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await crud.delete_question_type(db, type_id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при удалении типа вопроса") 