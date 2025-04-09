from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.crud import (
    create_test_question, delete_test_question, get_questions,
    get_question, create_question, update_question, delete_question, get_questions_by_test_id
)
from app.dependencies import get_db
from app.schemas import QuestionCreate, QuestionResponse, QuestionUpdate, QuestionWithDetails
from app.exceptions import NotFoundException, DatabaseException

router = APIRouter(prefix="/api/questions", tags=["Questions"])


# Получение списка всех вопросов
@router.get("/", response_model=list[QuestionResponse])
async def list_questions(db: AsyncSession = Depends(get_db)):
    return await get_questions(db)


# Получение конкретного вопроса по ID
@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question_by_id(question_id: int, db: AsyncSession = Depends(get_db)):
    question = await get_question(db, question_id)
    if not question:
        raise NotFoundException("Question not found")
    return question


@router.get("/by-test/{test_id}", response_model=list[QuestionWithDetails])
async def list_questions_by_test(test_id: int, db: AsyncSession = Depends(get_db)):
    questions = await get_questions_by_test_id(db, test_id)
    if not questions:
        raise NotFoundException("No questions found for this test")
    return questions


# Создание нового вопроса
@router.post("/", response_model=QuestionResponse)
async def create_new_question(question: QuestionCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await create_question(db, question)
    except SQLAlchemyError:
        raise DatabaseException("Error creating question")


# Обновление вопроса по ID
@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question_by_id(question_id: int, question: QuestionUpdate, db: AsyncSession = Depends(get_db)):
    try:
        updated_question = await update_question(db, question_id, question)
        if not updated_question:
            raise NotFoundException("Question not found")
        return updated_question
    except SQLAlchemyError:
        raise DatabaseException("Error updating question")


# Удаление вопроса по ID
@router.delete("/{question_id}", response_model=QuestionResponse)
async def delete_question_by_id(question_id: int, db: AsyncSession = Depends(get_db)):
    try:
        question = await delete_question(db, question_id)
        if not question:
            raise NotFoundException("Question not found")
        return question
    except SQLAlchemyError:
        raise DatabaseException("Error deleting question")


# Создание связи между тестом и вопросом
@router.post("/{question_id}/add-to-test/{test_id}", status_code=status.HTTP_201_CREATED)
async def link_test_question(test_id: int, question_id: int, position: int, required: bool, max_score: int, db: AsyncSession = Depends(get_db)):
    try:
        return await create_test_question(db, test_id, question_id, position, required, max_score)
    except SQLAlchemyError:
        raise DatabaseException("Error linking test and question")


# Удаление связи между тестом и вопросом
@router.delete("/{question_id}/remove-from-test/{test_id}", status_code=status.HTTP_200_OK)
async def unlink_test_question(test_id: int, question_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await delete_test_question(db, test_id, question_id)
        if not result:
            raise NotFoundException("Test-Question relation not found")
        return {"detail": "Test-Question relation deleted successfully", "data": result}
    except SQLAlchemyError:
        raise DatabaseException("Error unlinking test and question")
