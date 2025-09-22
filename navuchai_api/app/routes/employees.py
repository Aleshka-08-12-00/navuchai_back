from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import List

from app.dependencies import get_db
from app.crud.employee import get_employee_tree
from app.schemas.employee import EmployeeNode
from app.crud import authorized_required
from app.models import User
from app.exceptions import DatabaseException


router = APIRouter(prefix="/api/employees", tags=["Employees"])


@router.get("/tree/", response_model=List[EmployeeNode])
async def get_employees_tree(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        return await get_employee_tree(db)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении дерева сотрудников")


