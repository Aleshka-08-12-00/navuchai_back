from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class QuestionImportData(BaseModel):
    """Данные для импорта одного вопроса"""
    question_text: str
    question_abstract: str
    question_type: str  # SINGLE_CHOICE, MULTIPLE_CHOICE, etc.
    options: List[str]  # Варианты ответов
    correct_answers: List[str]  # Правильные ответы (индексы или тексты)
    position: int
    required: bool = True
    max_score: int = 1
    time_limit: Optional[int] = 0


class TestImportData(BaseModel):
    """Данные для импорта теста"""
    title: str
    description: Optional[str] = None
    category_name: str
    locale_code: str = "ru"
    time_limit: Optional[int] = None
    welcome_message: Optional[str] = None
    goodbye_message: Optional[str] = None
    answer_view_mode: str = "user_only"
    questions: List[QuestionImportData]


class TestImportResponse(BaseModel):
    """Ответ на импорт теста"""
    success: bool
    message: str
    test_id: Optional[int] = None
    imported_questions: int = 0
    errors: List[str] = [] 