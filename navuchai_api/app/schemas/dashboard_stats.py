from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DashboardStatsSchema(BaseModel):
    """Схема для статистики дашборда пользователя"""
    
    # Основная информация
    user_id: int
    user_name: str
    user_email: str
    
    # Группа тестов
    test_group_id: Optional[int] = None
    test_group_name: Optional[str] = None
    
    # Информация о тесте
    test_id: Optional[int] = None
    test_title: Optional[str] = None
    test_description: Optional[str] = None
    test_total_questions: Optional[int] = None
    
    # Категория теста
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    
    # Попытки прохождения
    attempts_used: Optional[int] = None
    total_attempts: Optional[int] = None
    attempts_remaining: Optional[int] = None
    
    # Временные рамки теста
    test_start_date: Optional[datetime] = None
    test_end_date: Optional[datetime] = None
    
    # Прохождение пользователем
    user_start_date: Optional[datetime] = None
    user_end_date: Optional[datetime] = None
    test_completed_at: Optional[datetime] = None
    
    # Результаты и время
    completion_time_minutes: Optional[int] = None
    user_score: Optional[int] = None
    completion_percent: Optional[float] = None
    
    # Статус прохождения
    test_status: Optional[str] = None
    is_test_completed: Optional[bool] = None
    
    # Группы и создатели
    user_group_id: Optional[int] = None
    user_group_name: Optional[str] = None
    test_creator_name: Optional[str] = None
    
    # Временные ограничения
    test_time_limit: Optional[int] = None
    test_group_time_limit: Optional[int] = None
    
    # Статистика пользователя
    user_total_tests_accessed: Optional[int] = None
    user_total_tests_completed: Optional[int] = None
    user_avg_score: Optional[float] = None
    user_best_score: Optional[int] = None
    user_worst_score: Optional[int] = None
    user_total_attempts: Optional[int] = None
    user_avg_completion_percent: Optional[float] = None
    user_first_test_date: Optional[datetime] = None
    user_last_test_date: Optional[datetime] = None
    user_questions_answered: Optional[int] = None
    user_test_groups_completed: Optional[int] = None
    
    # Рейтинги и сравнения
    user_rank_in_test: Optional[int] = None
    user_percentile_score: Optional[float] = None

    class Config:
        from_attributes = True
