from app.models import Result, UserAnswer
from app.schemas.result import ResultResponse, UserAnswerResponse
from datetime import datetime


def format_test_with_names(test, category_name: str, creator_name: str, locale_code: str, status_name: str, status_name_ru: str, status_color: str, access_status_name: str = None, access_status_code: str = None, access_status_color: str = None) -> dict:
    result = {
        "id": test.id,
        "title": test.title,
        "description": test.description,
        "category_id": test.category_id,
        "category_name": category_name,
        "creator_id": test.creator_id,
        "creator_name": creator_name,
        "access_timestamp": test.access_timestamp,
        "status_id": test.status_id,
        "status_name": status_name,
        "status_name_ru": status_name_ru,
        "status_color": status_color,
        "frozen": test.frozen,
        "locale_id": test.locale_id,
        "locale_code": locale_code,
        "time_limit": test.time_limit,
        "img_id": test.img_id,
        "thumbnail_id": test.thumbnail_id,
        "image": test.image,
        "thumbnail": test.thumbnail,
        "percent": test.avg_percent,
        "completed": test.completed_number,
        "welcome_message": test.welcome_message,
        "goodbye_message": test.goodbye_message,
        "created_at": test.created_at,
        "updated_at": test.updated_at,
        "access": test.access
    }
    
    if access_status_name is not None:
        result.update({
            "access_status_name": access_status_name,
            "access_status_code": access_status_code,
            "access_status_color": access_status_color
        })
    
    return result


def convert_user_answer(answer: UserAnswer) -> UserAnswerResponse:
    """Преобразует модель UserAnswer в схему UserAnswerResponse"""
    answer_data = answer.answer.copy()
    time_start = datetime.fromisoformat(answer_data.pop('time_start'))
    time_end = datetime.fromisoformat(answer_data.pop('time_end'))
    
    return UserAnswerResponse(
        id=answer.id,
        question_id=answer.question_id,
        user_id=answer.user_id,
        answer=answer_data,
        time_start=time_start,
        time_end=time_end,
        created_at=answer.created_at,
        updated_at=answer.updated_at
    )


def convert_result(result: Result) -> ResultResponse:
    """Преобразует модель Result в схему ResultResponse"""
    result_data = result.result.copy() if result.result else {}
    
    # Получаем время из result_data или используем completed_at как fallback
    time_start = None
    time_end = None
    
    if 'time_start' in result_data:
        try:
            time_start = datetime.fromisoformat(result_data['time_start'])
        except (ValueError, TypeError):
            time_start = result.completed_at
    
    if 'time_end' in result_data:
        try:
            time_end = datetime.fromisoformat(result_data['time_end'])
        except (ValueError, TypeError):
            time_end = result.completed_at
    
    # Если время не найдено, используем completed_at
    if not time_start:
        time_start = result.completed_at
    if not time_end:
        time_end = result.completed_at
    
    # Удаляем поля времени из result_data, так как они уже обработаны
    result_data.pop('time_start', None)
    result_data.pop('time_end', None)
    
    return ResultResponse(
        id=result.id,
        user_id=result.user_id,
        test_id=result.test_id,
        score=result.score,
        result=result_data,
        time_start=time_start,
        time_end=time_end,
        completed_at=result.completed_at,
        created_at=result.created_at,
        updated_at=result.updated_at
    ) 