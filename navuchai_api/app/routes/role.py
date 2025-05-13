from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import authorized_required
from app.crud import role as role_crud
from app.dependencies import get_db
from app.models import User
from app.schemas.role import RoleInDB

router = APIRouter(prefix="/api/roles", tags=["Roles"])


@router.get("/", response_model=list[RoleInDB])
async def get_roles(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    return await role_crud.get_roles(db=db)
