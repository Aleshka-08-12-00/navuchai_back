from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.schemas.analytics_views import AnalyticsViewSchema
from app.crud.analytics import get_all_analytics_views
from app.crud import root_admin_moderator_required, authorized_required
from app.models import User

router = APIRouter(prefix="/api/analytics_views", tags=["AnalyticsViews"])


@router.get("/", response_model=list[AnalyticsViewSchema])
async def get_analytics_views(db: AsyncSession = Depends(get_db),
                              current_user: User = Depends(root_admin_moderator_required)):
    return await get_all_analytics_views(db)


@router.get("/user/me/chart", response_model=dict)
async def get_my_tests_chart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    from app.crud.analytics import get_user_tests_chart_config
    return await get_user_tests_chart_config(db, current_user.id, limit=10)


@router.get("/user/me/pie", response_model=list[dict])
async def get_my_tests_pie(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    from app.crud.analytics import get_user_tests_pie_config
    return await get_user_tests_pie_config(db, current_user.id, limit=5)
