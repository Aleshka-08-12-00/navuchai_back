from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from typing import List, Dict, Any

from app.crud import (
    create_test_question, delete_test_question, get_questions,
    get_question, create_question, update_question, delete_question, get_questions_by_test_id, root_admin_moderator_required, authorized_required, copy_question_to_test
)
from app.dependencies import get_db
from app.schemas import QuestionCreate, QuestionResponse, QuestionUpdate, QuestionWithDetails
from app.schemas.test_question import TestQuestionCreate
from app.exceptions import NotFoundException, DatabaseException
from app.models import User
from app.utils.test_generator import generate_test_questions

router = APIRouter(prefix="/api/questions", tags=["Questions"])


class TextGenerationRequest(BaseModel):
    source_text: str
    questions_count: int


class GeneratedQuestionResponse(BaseModel):
    text: str
    text_abstract: str
    type_id: int
    reviewable: bool
    answers: Dict[str, Any]


# Получение списка всех вопросов
@router.get("/", response_model=list[QuestionResponse])
async def get_all_questions(db: AsyncSession = Depends(get_db), user: User = Depends(authorized_required)):
    try:
        return await get_questions(db)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка вопросов")


# Получение конкретного вопроса по ID
@router.get("/{question_id}/", response_model=QuestionResponse)
async def get_question_by_id(question_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(authorized_required)):
    try:
        question = await get_question(db, question_id)
        if not question:
            raise NotFoundException("Вопрос не найден")
        return question
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении вопроса")


@router.get("/by-test/{test_id}/", response_model=list[QuestionWithDetails])
async def list_questions_by_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(authorized_required)
):
    questions = await get_questions_by_test_id(db, test_id)
    if not questions:
        raise NotFoundException("No questions found for this test")
    return questions


@router.get("/by-test/{test_id}/public/", response_model=list[QuestionWithDetails])
async def list_questions_by_test_public(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(authorized_required)
):
    """
    Получение вопросов теста без правильных ответов для публичного доступа
    """
    questions = await get_questions_by_test_id(db, test_id)
    if not questions:
        raise NotFoundException("No questions found for this test")
    
    # Преобразуем вопросы в словари и удаляем correctAnswer
    result = []
    for question in questions:
        # Преобразуем объект Question в словарь
        question_dict = {
            'question': {
                'id': question['question'].id,
                'text': question['question'].text,
                'text_abstract': question['question'].text_abstract,
                'type_id': question['question'].type_id,
                'type': question['question'].type,
                'reviewable': question['question'].reviewable,
                'answers': question['question'].answers,
                'time_limit': question['question'].time_limit,
                'created_at': question['question'].created_at,
                'updated_at': question['question'].updated_at
            },
            'position': question['position'],
            'required': question['required'],
            'max_score': question['max_score']
        }
        
        # Удаляем правильные ответы
        if 'answers' in question_dict['question']:
            answers = question_dict['question']['answers']
            if 'correctAnswer' in answers:
                del answers['correctAnswer']
            if 'correct' in answers:
                del answers['correct']
        
        result.append(question_dict)
    
    return result


# Создание нового вопроса
@router.post("/", response_model=QuestionResponse)
async def create_new_question(question: QuestionCreate, db: AsyncSession = Depends(get_db), user: User = Depends(root_admin_moderator_required)):
    try:
        return await create_question(db, question)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании вопроса")


# Обновление вопроса по ID
@router.put("/{question_id}/", response_model=QuestionResponse)
async def update_question_by_id(question_id: int, question: QuestionUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(root_admin_moderator_required)):
    try:
        updated_question = await update_question(db, question_id, question)
        if not updated_question:
            raise NotFoundException("Вопрос не найден")
        return updated_question
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении вопроса")


# Удаление вопроса по ID
@router.delete("/{question_id}/", response_model=QuestionResponse)
async def delete_question_by_id(question_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(root_admin_moderator_required)):
    try:
        question = await delete_question(db, question_id)
        if not question:
            raise NotFoundException("Вопрос не найден")
        return question
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при удалении вопроса")


# Создание связи между тестом и вопросом
@router.post("/{question_id}/add-to-test/{test_id}/", status_code=status.HTTP_201_CREATED)
async def link_test_question(
    test_id: int, 
    question_id: int, 
    test_question_data: TestQuestionCreate = TestQuestionCreate(),
    db: AsyncSession = Depends(get_db), 
    user: User = Depends(root_admin_moderator_required)
):
    try:
        return await create_test_question(
            db, 
            test_id, 
            question_id, 
            position=test_question_data.position,
            required=test_question_data.required
        )
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при связывании теста и вопроса")


# Удаление связи между тестом и вопросом
@router.delete("/{question_id}/remove-from-test/{test_id}/", status_code=status.HTTP_200_OK)
async def unlink_test_question(test_id: int, question_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(root_admin_moderator_required)):
    try:
        result = await delete_test_question(db, test_id, question_id)
        if not result:
            raise NotFoundException("Test-Question relation not found")
        return {"detail": "Test-Question relation deleted successfully", "data": result}
    except SQLAlchemyError:
        raise DatabaseException("Error unlinking test and question")


# Копирование вопроса в тест
@router.post("/{question_id}/copy-to-test/{test_id}/", response_model=QuestionResponse)
async def copy_question_to_test_route(
    question_id: int,
    test_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(root_admin_moderator_required)
):
    try:
        # 1) Получаем исходный вопрос (ORM модель)
        source = await get_question(db, question_id)
        # 2) Создаем новый вопрос через существующий CRUD
        payload = QuestionCreate(
            text=source.text,
            text_abstract=source.text_abstract,
            type_id=source.type_id,
            reviewable=source.reviewable,
            answers=source.answers,
            time_limit=source.time_limit,
        )
        created = await create_question(db, payload)
        # 3) Привязываем новый вопрос к тесту существующим методом
        await create_test_question(db, test_id, created.id)
        # 4) Возвращаем новый вопрос с предзагруженным type
        return await get_question(db, created.id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при копировании вопроса в тест")


#Генерация тестовых вопросов на основе текста
@router.post("/generate-from-text/", response_model=List[GeneratedQuestionResponse])
async def generate_questions_from_text(
    request: TextGenerationRequest,
    user: User = Depends(root_admin_moderator_required)
):
    """
    Генерирует тестовые вопросы на основе предоставленного текста с помощью Yandex Cloud ML
    """
    try:
        questions = generate_test_questions(request.source_text, request.questions_count)
        return questions
    except Exception as e:
        raise DatabaseException(f"Ошибка при генерации вопросов: {str(e)}")
