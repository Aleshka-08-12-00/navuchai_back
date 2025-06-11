from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.dependencies import get_db
from app.crud import test_status as crud_test_status
from app.schemas.test_status import TestStatusResponse
from app.exceptions import DatabaseException
from app.crud import authorized_required
from app.models.user import User

router = APIRouter(
    prefix="/api/test-statuses",
    tags=["Test Statuses"]
)


@router.get("/", response_model=List[TestStatusResponse])
async def read_test_statuses(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        statuses = await crud_test_status.get_test_statuses(db)
        return statuses
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Непредвиденная ошибка: {str(e)}")
