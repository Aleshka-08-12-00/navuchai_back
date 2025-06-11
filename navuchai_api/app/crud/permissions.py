from fastapi import Depends
from app.models.role_enum import RoleCode
from app.models import User
from app.crud.user_auth import get_current_user
from app.exceptions import ForbiddenException


def role_required(*allowed_roles: RoleCode):
    async def checker(user: User = Depends(get_current_user)):
        if not user.role or user.role.code not in allowed_roles:
            raise ForbiddenException("У вас нет прав для доступа к этому ресурсу")
        return user
    return checker


admin_required = role_required(RoleCode.ADMIN)
moderator_required = role_required(RoleCode.MODERATOR)
admin_moderator_required = role_required(RoleCode.ADMIN, RoleCode.MODERATOR)
user_required = role_required(RoleCode.USER)
authorized_required = role_required(RoleCode.ADMIN, RoleCode.MODERATOR, RoleCode.USER)
