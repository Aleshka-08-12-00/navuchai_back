from app.models import Result, UserAnswer
from app.schemas.result import ResultResponse, UserAnswerResponse
from app.schemas.test import TestResponse
from app.schemas.user import UserResponse
from app.schemas.role import RoleBase
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Union, Any, Dict


def filter_answers_by_view_mode(result_data: Dict[str, Any], user_role_code: str, test_answer_view_mode: str) -> Dict[str, Any]:
    """
    Фильтрует ответы в результате в зависимости от роли пользователя и настроек теста
    
    Args:
        result_data: Данные результата теста
        user_role_code: Код роли пользователя ('admin', 'moderator', 'user')
        test_answer_view_mode: Режим показа ответов теста ('user_only', 'none', 'user_and_correct')
    
    Returns:
        Отфильтрованные данные результата
    """
    # Админы и модераторы видят все ответы
    if user_role_code in ["admin", "moderator"]:
        return result_data
    
    # Для обычных пользователей применяем фильтрацию
    if user_role_code == "user":
        if 'checked_answers' in result_data:
            filtered_answers = []
            for answer in result_data['checked_answers']:
                filtered_answer = answer.copy()
                
                if test_answer_view_mode == 'user_only':
                    # Показывать только ответы пользователя
                    if 'options' in filtered_answer:
                        filtered_answer['options'] = filtered_answer['options'].copy()
                        # Очищаем correctAnswer
                        if 'correctAnswer' in filtered_answer['options']:
                            filtered_answer['options']['correctAnswer'] = []
                        # Очищаем allAnswer
                        if 'allAnswer' in filtered_answer['options']:
                            filtered_answer['options']['allAnswer'] = []
                    
                    # В check_details оставляем только user_answer/user_answers
                    if 'check_details' in filtered_answer:
                        filtered_answer['check_details'] = filtered_answer['check_details'].copy()
                        if 'correct_answer' in filtered_answer['check_details']:
                            filtered_answer['check_details']['correct_answer'] = ""
                        if 'correct_answers' in filtered_answer['check_details']:
                            filtered_answer['check_details']['correct_answers'] = []
                
                elif test_answer_view_mode == 'none':
                    # Не показывать ответы вообще
                    if 'options' in filtered_answer:
                        filtered_answer['options'] = filtered_answer['options'].copy()
                        # Очищаем correctAnswer
                        if 'correctAnswer' in filtered_answer['options']:
                            filtered_answer['options']['correctAnswer'] = []
                        # Очищаем allAnswer
                        if 'allAnswer' in filtered_answer['options']:
                            filtered_answer['options']['allAnswer'] = []
                    
                    # Очищаем check_details
                    if 'check_details' in filtered_answer:
                        filtered_answer['check_details'] = {}
                
                elif test_answer_view_mode == 'user_and_correct':
                    # Показывать ответы пользователя с правильным ответом (оставляем как есть)
                    pass
                
                filtered_answers.append(filtered_answer)
            
            result_data = result_data.copy()
            result_data['checked_answers'] = filtered_answers
    
    return result_data


def format_test_with_names(test, category_name: str, creator_name: str, locale_code: str, status_name: str, status_name_ru: str, status_color: str, access_status_name: str = None, access_status_code: str = None, access_status_color: str = None, user_completed: int = None, user_percent: int = None, access_code: str = None, is_completed: bool = None) -> dict:
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
        "access": test.access,
        "answer_view_mode": test.answer_view_mode,
        "code": test.code,
        "access_code": access_code,
    }
    
    if access_status_name is not None:
        result.update({
            "access_status_name": access_status_name,
            "access_status_code": access_status_code,
            "access_status_color": access_status_color
        })
    
    if user_percent is not None:
        result["user_percent"] = user_percent
    
    if user_completed is not None:
        result["user_completed"] = user_completed
    
    # Если is_completed не установлено (None), то done = false, иначе используем значение is_completed
    result["done"] = is_completed if is_completed is not None else False
    
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


def user_to_response_dict(user):
    return {
        "id": user.id,
        "name": user.name,
        "role_id": user.role_id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "photo_url": user.img.path if hasattr(user, 'img') and user.img else None,
        "organization": user.organization.name if hasattr(user, 'organization') and user.organization else None,
        "position": user.position.name if hasattr(user, 'position') and user.position else None,
        "department": user.department.name if hasattr(user, 'department') and user.department else None,
        "phone_number": user.phone_number,
        "role": RoleBase.model_validate(user.role, from_attributes=True) if user.role else None,
    }


def convert_result(result: Result, current_user: Any = None) -> ResultResponse:
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
    
    # Применяем фильтрацию ответов в зависимости от роли пользователя и настроек теста
    if current_user and result.test:
        user_role_code = current_user.role.code if current_user.role else "user"
        test_answer_view_mode = result.test.answer_view_mode.value if result.test.answer_view_mode else "user_only"
        result_data = filter_answers_by_view_mode(result_data, user_role_code, test_answer_view_mode)
    # Если current_user не передан, показываем все ответы (для обратной совместимости)
    
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
        updated_at=result.updated_at,
        test=TestResponse.model_validate(result.test, from_attributes=True) if result.test else None,
        user=UserResponse.model_validate(user_to_response_dict(result.user)) if result.user else None,
    )


def format_numeric_value(value: Any) -> Union[float, int, Any]:
    """
    Форматирует числовое значение для Excel отчета:
    - Округляет до сотых (2 знака после запятой)
    - Заменяет 0E-20 и подобные значения на 0
    - Возвращает исходное значение для нечисловых данных
    
    Args:
        value: Значение для форматирования
        
    Returns:
        Отформатированное значение
    """
    # Проверяем, является ли значение числовым
    if pd.isna(value) or value is None:
        return 0.0
    
    # Проверяем на научную нотацию (например, 0E-20)
    if isinstance(value, (int, float)):
        # Заменяем очень маленькие числа на 0
        if abs(value) < 1e-10:
            return 0.0
        # Округляем до сотых
        return round(value, 2)
    
    # Для строк - проверяем, можно ли преобразовать в число
    if isinstance(value, str):
        try:
            num_value = float(value)
            # Заменяем очень маленькие числа на 0
            if abs(num_value) < 1e-10:
                return 0.0
            # Округляем до сотых
            return round(num_value, 2)
        except (ValueError, TypeError):
            return value
    
    return value


def format_dataframe_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Форматирует DataFrame для экспорта в Excel:
    - Округляет числовые колонки до сотых
    - Заменяет 0E-20 и подобные значения на 0
    - Сохраняет исходные типы данных для нечисловых колонок
    
    Args:
        df: DataFrame для форматирования
        
    Returns:
        Отформатированный DataFrame
    """
    df_formatted = df.copy()
    
    for column in df_formatted.columns:
        # Проверяем, является ли колонка числовой
        if df_formatted[column].dtype in ['float64', 'int64', 'float32', 'int32']:
            # Применяем форматирование к числовым колонкам
            df_formatted[column] = df_formatted[column].apply(format_numeric_value)
        elif df_formatted[column].dtype == 'object':
            # Для объектных колонок проверяем, можно ли преобразовать в числа
            try:
                # Пробуем преобразовать в числовой тип
                numeric_series = pd.to_numeric(df_formatted[column], errors='coerce')
                # Если большинство значений числовые, применяем форматирование
                if numeric_series.notna().sum() > len(df_formatted) * 0.5:
                    df_formatted[column] = df_formatted[column].apply(format_numeric_value)
            except (ValueError, TypeError):
                # Если не удалось преобразовать, оставляем как есть
                pass
    
    return df_formatted


def get_numeric_columns_for_formatting(df: pd.DataFrame) -> list:
    """
    Определяет числовые колонки, которые нужно форматировать,
    основываясь на названиях колонок и типах данных
    
    Args:
        df: DataFrame для анализа
        
    Returns:
        Список названий числовых колонок
    """
    numeric_keywords = [
        'средний', 'avg', 'total', 'всего', 'дней', 'балл', 'score', 
        'процент', 'percent', 'попыт', 'attempt', 'вопрос', 'question',
        'лимит', 'limit', 'время', 'time', 'актив', 'active', 'заверш',
        'complete', 'доступ', 'access', 'правиль', 'correct', 'неправиль',
        'incorrect', 'отклонение', 'stddev', 'минималь', 'min', 'максималь', 'max'
    ]
    
    numeric_columns = []
    
    for column in df.columns:
        column_lower = str(column).lower()
        
        # Проверяем по типу данных
        is_numeric_type = df[column].dtype in ['float64', 'int64', 'float32', 'int32']
        
        # Проверяем по ключевым словам в названии
        has_numeric_keyword = any(keyword in column_lower for keyword in numeric_keywords)
        
        # Проверяем, можно ли преобразовать в число
        try:
            numeric_series = pd.to_numeric(df[column], errors='coerce')
            can_be_numeric = numeric_series.notna().sum() > len(df) * 0.5
        except:
            can_be_numeric = False
        
        if is_numeric_type or has_numeric_keyword or can_be_numeric:
            numeric_columns.append(column)
    
    return numeric_columns


def apply_excel_formatting(df: pd.DataFrame, numeric_columns: list = None) -> pd.DataFrame:
    """
    Применяет форматирование для Excel отчета:
    - Если numeric_columns не указан, автоматически определяет числовые колонки
    - Округляет до сотых и заменяет 0E-20 на 0
    
    Args:
        df: DataFrame для форматирования
        numeric_columns: Список числовых колонок (опционально)
        
    Returns:
        Отформатированный DataFrame
    """
    if numeric_columns is None:
        numeric_columns = get_numeric_columns_for_formatting(df)
    
    df_formatted = df.copy()
    
    for column in numeric_columns:
        if column in df_formatted.columns:
            df_formatted[column] = df_formatted[column].apply(format_numeric_value)
    
    return df_formatted 