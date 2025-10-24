from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.schemas.dashboard_stats import DashboardStatsSchema
from app.crud.dashboard_stats import get_dashboard_stats_by_user_id, get_dashboard_stats_summary
from app.crud import authorized_required
from app.models import User
from typing import List, Dict, Any

router = APIRouter(prefix="/api/dashboard-stats", tags=["DashboardStats"])


@router.get("/user/{user_id}", response_model=List[DashboardStatsSchema])
async def get_dashboard_stats(
    user_id: int = Path(..., description="ID пользователя для получения статистики"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    """
    Получение детальной статистики дашборда для конкретного пользователя.
    
    Возвращает полную информацию о всех тестах пользователя, включая:
    - Основную информацию о пользователе
    - Информацию о тестах и группах тестов
    - Статистику прохождения
    - Рейтинги и сравнения
    """
    try:
        return await get_dashboard_stats_by_user_id(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении статистики: {str(e)}")


@router.get("/user/{user_id}/summary", response_model=Dict[str, Any])
async def get_dashboard_stats_summary_endpoint(
    user_id: int = Path(..., description="ID пользователя для получения сводной статистики"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    """
    Получение сводной статистики пользователя для дашборда.
    
    Возвращает общую статистику пользователя без детализации по отдельным тестам.
    """
    try:
        return await get_dashboard_stats_summary(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении сводной статистики: {str(e)}")


@router.get("/me", response_model=List[DashboardStatsSchema])
async def get_my_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    """
    Получение статистики дашборда для текущего авторизованного пользователя.
    """
    try:
        return await get_dashboard_stats_by_user_id(db, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении статистики: {str(e)}")


@router.get("/me/summary", response_model=Dict[str, Any])
async def get_my_dashboard_stats_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    """
    Получение сводной статистики для текущего авторизованного пользователя.
    """
    try:
        return await get_dashboard_stats_summary(db, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении сводной статистики: {str(e)}")
