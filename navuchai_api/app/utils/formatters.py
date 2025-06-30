from app.models import Result, UserAnswer
from app.schemas.result import ResultResponse, UserAnswerResponse
from datetime import datetime
import pandas as pd
import numpy as np
from typing import Union, Any


def format_test_with_names(test, category_name: str, creator_name: str, locale_code: str, status_name: str, status_name_ru: str, status_color: str, access_status_name: str = None, access_status_code: str = None, access_status_color: str = None, user_completed: int = None, user_percent: int = None) -> dict:
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
    
    if user_percent is not None:
        result["user_percent"] = user_percent
    
    if user_completed is not None:
        result["user_completed"] = user_completed
    
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