from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.crud import get_users, get_user, update_user, delete_user, admin_moderator_required, admin_required, update_user_role, authorized_required, reset_user_password
from app.dependencies import get_db
from app.exceptions import NotFoundException, DatabaseException, ForbiddenException
from app.schemas.user import UserResponse, UserUpdate, UserRoleUpdate, PasswordResetRequest, PasswordResetResponse
from app.models import User
from app.utils.email_service import email_service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse], dependencies=[Depends(admin_moderator_required)])
async def list_users(db: AsyncSession = Depends(get_db)):
    return await get_users(db)


@router.get("/{user_id}/", response_model=UserResponse)
async def get_user_by_id(
    user_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        # Проверяем права доступа
        if current_user.role.code not in ["admin", "moderator"] and current_user.id != user_id:
            raise ForbiddenException("Нет доступа к информации о другом пользователе")
            
        user = await get_user(db, user_id)
        if not user:
            raise NotFoundException("Пользователь не найден")
        return user
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении данных пользователя")


@router.put("/{user_id}/", response_model=UserResponse, dependencies=[Depends(admin_moderator_required)])
async def update_user_by_id(user_id: int, update_data: UserUpdate, db: AsyncSession = Depends(get_db)):
    try:
        updated = await update_user(db, user_id, update_data)
        if not updated:
            raise NotFoundException("Пользователь не найден")
        return updated
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при обновлении данных пользователя")


@router.delete("/{user_id}/", response_model=UserResponse, dependencies=[Depends(admin_moderator_required)])
async def delete_user_by_id(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        deleted = await delete_user(db, user_id)
        if not deleted:
            raise NotFoundException("Пользователь не найден")
        return deleted
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при удалении пользователя")


@router.put("/{user_id}/role/", dependencies=[Depends(admin_required)])
async def change_user_role(
    user_id: int,
    update_role: UserRoleUpdate,  # <-- вот здесь
    db: AsyncSession = Depends(get_db),
):
    user = await update_user_role(db, user_id, update_role.role_code.value)
    return {
        "message": f"User role updated",
        "user_id": user.id,
        "new_role": update_role.role_code.value
    }


@router.post("/reset-password/", response_model=PasswordResetResponse)
async def reset_password(
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Восстановление пароля пользователя
    
    Отправляет новый временный пароль на email пользователя.
    Доступно только для зарегистрированных пользователей (не гостей).
    """
    try:
        result = await reset_user_password(db, reset_request.email)
        return PasswordResetResponse(
            message=result["message"],
            success=result["success"]
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Неожиданная ошибка: {str(e)}")


@router.post("/test-email/", dependencies=[Depends(admin_required)])
async def test_email_settings(
    reset_request: PasswordResetRequest
):
    """
    Тестирование настроек email
    
    Отправляет тестовое письмо для проверки конфигурации email.
    Доступно только для администраторов.
    """
    try:
        await email_service.send_test_email(reset_request.email)
        return {
            "message": f"Тестовое письмо отправлено на {reset_request.email}",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке тестового письма: {str(e)}")
