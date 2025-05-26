from app.models import Result, UserAnswer
from app.schemas.result import ResultResponse, UserAnswerResponse


def format_test_with_names(test, category_name: str, creator_name: str, locale_code: str, status_name: str, status_name_ru: str, status_color: str) -> dict:
    return {
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
        "image": test.image,
        "percent": test.avg_percent,
        "completed": test.completed_number,
        "welcome_message": test.welcome_message,
        "goodbye_message": test.goodbye_message,
        "created_at": test.created_at,
        "updated_at": test.updated_at,
        "access": test.access
    }


# def format_user(user, role_name: str) -> dict:
#     return {
#         "id": user.id,
#         "name": user.name,
#         "username": user.username,
#         "email": user.email,
#         "role_id": user.role_id,
#         "role_name": role_name,
#         "created_at": user.created_at,
#         "updated_at": user.updated_at
#     }


def convert_user_answer(answer: UserAnswer) -> UserAnswerResponse:
    """Преобразует модель UserAnswer в схему UserAnswerResponse"""
    return UserAnswerResponse(
        id=answer.id,
        result_id=answer.result_id,
        question_id=answer.question_id,
        user_id=answer.user_id,
        options=answer.options,
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
