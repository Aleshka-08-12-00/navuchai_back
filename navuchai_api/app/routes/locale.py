from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models import User
from app.crud import admin_moderator_required
from app.crud import locale as locale_crud
from app.schemas.locale import LocaleInDB

router = APIRouter(prefix="/api/locales", tags=["Locales"])


@router.get("/", response_model=list[LocaleInDB])
async def get_locales(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(admin_moderator_required)
):
    return await locale_crud.get_locales(db=db)
