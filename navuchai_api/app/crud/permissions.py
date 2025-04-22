from fastapi import Depends, HTTPException, status
from app.models.role_enum import RoleCode
from app.models import User
from app.crud.user_auth import get_current_user


def role_required(*allowed_roles: RoleCode):
    async def checker(user: User = Depends(get_current_user)):
        if not user.role or user.role.code not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource"
            )
        return user
    return checker


admin_required = role_required(RoleCode.ADMIN)
teacher_required = role_required(RoleCode.TEACHER)
admin_teacher_required = role_required(RoleCode.ADMIN, RoleCode.TEACHER)
student_required = role_required(RoleCode.STUDENT)
authorized_required = role_required(RoleCode.ADMIN, RoleCode.TEACHER, RoleCode.STUDENT)
