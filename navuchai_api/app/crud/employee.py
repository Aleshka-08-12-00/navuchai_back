from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List

from app.models import Employee
from app.exceptions import DatabaseException


async def get_employee_tree(db: AsyncSession) -> List[Dict]:
    try:
        result = await db.execute(select(Employee))
        employees = result.scalars().all()

        by_id: Dict[int, Employee] = {e.id: e for e in employees}

        children_map: Dict[int, List[Employee]] = {}
        for e in employees:
            parent_id = e.parent_id or 0
            children_map.setdefault(parent_id, []).append(e)

        def make_node(emp: Employee, level: int) -> Dict:
            node = {
                "id": str(emp.id),
                "name": emp.name,
                "position": emp.position,
                "department": emp.department,
                "email": emp.email,
                "phone": emp.phone,
                "level": level,
                "children": []
            }
            for child in children_map.get(emp.id, []):
                node["children"].append(make_node(child, level + 1))
            return node

        roots: List[Dict] = []
        for e in employees:
            if (e.parent_id or 0) == 0 or e.parent_id not in by_id:
                roots.append(make_node(e, 0))

        return roots
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении дерева сотрудников: {str(e)}")


