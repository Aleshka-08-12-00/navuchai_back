from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.schemas.analytics_views import AnalyticsViewSchema
from app.crud.analytics import get_all_analytics_views
from app.crud import admin_moderator_required
from app.models import User

router = APIRouter(prefix="/api/analytics_views", tags=["AnalyticsViews"])


@router.get("/", response_model=list[AnalyticsViewSchema])
async def get_analytics_views(db: AsyncSession = Depends(get_db),
                              current_user: User = Depends(admin_moderator_required)):
    return await get_all_analytics_views(db)
