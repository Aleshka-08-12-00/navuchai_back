from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.exceptions import DatabaseException
from app.schemas.dashboard_stats import DashboardStatsSchema


async def get_dashboard_stats_by_user_id(db: AsyncSession, user_id: int) -> List[DashboardStatsSchema]:
    """Получение статистики дашборда для конкретного пользователя из вьюхи analytics_dashboard"""
    try:
        # Запрос к существующей вьюхе analytics_dashboard
        stmt = text("""
        SELECT 
            user_id,
            user_name,
            user_email,
            test_group_id,
            test_group_name,
            test_id,
            test_title,
            test_description,
            test_total_questions,
            category_id,
            category_name,
            attempts_used,
            total_attempts,
            attempts_remaining,
            test_start_date,
            test_end_date,
            user_start_date,
            user_end_date,
            test_completed_at,
            completion_time_minutes,
            user_score,
            completion_percent,
            test_status,
            is_test_completed,
            user_group_id,
            user_group_name,
            test_creator_name,
            test_time_limit,
            test_group_time_limit,
            user_total_tests_accessed,
            user_total_tests_completed,
            user_avg_score,
            user_best_score,
            user_worst_score,
            user_total_attempts,
            user_avg_completion_percent,
            user_first_test_date,
            user_last_test_date,
            user_questions_answered,
            user_test_groups_completed,
            user_rank_in_test,
            user_percentile_score
        FROM analytics_dashboard
        WHERE user_id = :user_id
        ORDER BY test_id
        """)
        
        result = await db.execute(stmt, {"user_id": user_id})
        rows = result.fetchall()
        
        # Преобразуем результаты в список схем
        dashboard_stats = []
        for row in rows:
            dashboard_stats.append(DashboardStatsSchema(
                user_id=row.user_id,
                user_name=row.user_name,
                user_email=row.user_email,
                test_group_id=row.test_group_id,
                test_group_name=row.test_group_name,
                test_id=row.test_id,
                test_title=row.test_title,
                test_description=row.test_description,
                test_total_questions=row.test_total_questions,
                category_id=row.category_id,
                category_name=row.category_name,
                attempts_used=row.attempts_used,
                total_attempts=row.total_attempts,
                attempts_remaining=row.attempts_remaining,
                test_start_date=row.test_start_date,
                test_end_date=row.test_end_date,
                user_start_date=row.user_start_date,
                user_end_date=row.user_end_date,
                test_completed_at=row.test_completed_at,
                completion_time_minutes=row.completion_time_minutes,
                user_score=row.user_score,
                completion_percent=row.completion_percent,
                test_status=row.test_status,
                is_test_completed=row.is_test_completed,
                user_group_id=row.user_group_id,
                user_group_name=row.user_group_name,
                test_creator_name=row.test_creator_name,
                test_time_limit=row.test_time_limit,
                test_group_time_limit=row.test_group_time_limit,
                user_total_tests_accessed=row.user_total_tests_accessed,
                user_total_tests_completed=row.user_total_tests_completed,
                user_avg_score=row.user_avg_score,
                user_best_score=row.user_best_score,
                user_worst_score=row.user_worst_score,
                user_total_attempts=row.user_total_attempts,
                user_avg_completion_percent=row.user_avg_completion_percent,
                user_first_test_date=row.user_first_test_date,
                user_last_test_date=row.user_last_test_date,
                user_questions_answered=row.user_questions_answered,
                user_test_groups_completed=row.user_test_groups_completed,
                user_rank_in_test=row.user_rank_in_test,
                user_percentile_score=row.user_percentile_score
            ))
        
        return dashboard_stats
        
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении статистики дашборда: {str(e)}")


async def get_dashboard_stats_summary(db: AsyncSession, user_id: int) -> Dict[str, Any]:
    """Получение сводной статистики пользователя для дашборда из вьюхи analytics_dashboard"""
    try:
        stmt = text("""
        SELECT DISTINCT
            user_id,
            user_name,
            user_email,
            user_total_tests_accessed,
            user_total_tests_completed,
            user_avg_score,
            user_best_score,
            user_worst_score,
            user_total_attempts,
            user_avg_completion_percent,
            user_first_test_date,
            user_last_test_date,
            user_questions_answered,
            user_test_groups_completed
        FROM analytics_dashboard
        WHERE user_id = :user_id
        LIMIT 1
        """)
        
        result = await db.execute(stmt, {"user_id": user_id})
        row = result.fetchone()
        
        if not row:
            raise DatabaseException(f"Пользователь с ID {user_id} не найден в analytics_dashboard")
        
        return {
            "user_id": row.user_id,
            "user_name": row.user_name,
            "user_email": row.user_email,
            "total_tests_accessed": row.user_total_tests_accessed or 0,
            "total_tests_completed": row.user_total_tests_completed or 0,
            "avg_score": float(row.user_avg_score) if row.user_avg_score is not None else None,
            "best_score": row.user_best_score,
            "worst_score": row.user_worst_score,
            "total_attempts": row.user_total_attempts or 0,
            "avg_completion_percent": float(row.user_avg_completion_percent) if row.user_avg_completion_percent is not None else None,
            "first_test_date": row.user_first_test_date,
            "last_test_date": row.user_last_test_date,
            "total_questions_answered": row.user_questions_answered or 0,
            "test_groups_completed": row.user_test_groups_completed or 0
        }
        
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении сводной статистики: {str(e)}")
