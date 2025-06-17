from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.crud import (
    create_test_question, delete_test_question, get_questions,
    get_question, create_question, update_question, delete_question, get_questions_by_test_id, admin_moderator_required, authorized_required
)
from app.dependencies import get_db
from app.schemas import QuestionCreate, QuestionResponse, QuestionUpdate, QuestionWithDetails
from app.exceptions import NotFoundException, DatabaseException
from app.models import User

router = APIRouter(prefix="/api/questions", tags=["Questions"])


# Получение списка всех вопросов
@router.get("/", response_model=list[QuestionResponse])
async def get_all_questions(db: AsyncSession = Depends(get_db), user: User = Depends(authorized_required)):
    try:
        return await get_questions(db)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка вопросов")


# Получение конкретного вопроса по ID
@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question_by_id(question_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(authorized_required)):
    try:
        question = await get_question(db, question_id)
        if not question:
            raise NotFoundException("Вопрос не найден")
        return question
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении вопроса")


@router.get("/by-test/{test_id}", response_model=list[QuestionWithDetails])
async def list_questions_by_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(authorized_required)
):
    questions = await get_questions_by_test_id(db, test_id)
    if not questions:
        raise NotFoundException("No questions found for this test")
    return questions


@router.get("/by-test/{test_id}/public", response_model=list[QuestionWithDetails])
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
async def create_new_question(question: QuestionCreate, db: AsyncSession = Depends(get_db), user: User = Depends(admin_moderator_required)):
    try:
        return await create_question(db, question)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при создании вопроса")


# Обновление вопроса по ID
@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question_by_id(question_id: int, question: QuestionUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(admin_moderator_required)):
    try:
        updated_question = await update_question(db, question_id, question)
        if not updated_question:
            raise NotFoundException("Вопрос не найден")
        return updated_question
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении вопроса")


# Удаление вопроса по ID
@router.delete("/{question_id}", response_model=QuestionResponse)
async def delete_question_by_id(question_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(admin_moderator_required)):
    try:
        question = await delete_question(db, question_id)
        if not question:
            raise NotFoundException("Вопрос не найден")
        return question
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при удалении вопроса")


# Создание связи между тестом и вопросом
@router.post("/{question_id}/add-to-test/{test_id}", status_code=status.HTTP_201_CREATED)
async def link_test_question(test_id: int, question_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(admin_moderator_required)):
    try:
        return await create_test_question(db, test_id, question_id)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при связывании теста и вопроса")


# Удаление связи между тестом и вопросом
@router.delete("/{question_id}/remove-from-test/{test_id}", status_code=status.HTTP_200_OK)
async def unlink_test_question(test_id: int, question_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(admin_moderator_required)):
    try:
        result = await delete_test_question(db, test_id, question_id)
        if not result:
            raise NotFoundException("Test-Question relation not found")
        return {"detail": "Test-Question relation deleted successfully", "data": result}
    except SQLAlchemyError:
        raise DatabaseException("Error unlinking test and question")
