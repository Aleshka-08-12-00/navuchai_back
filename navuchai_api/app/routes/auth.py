from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.auth import verify_password, create_access_token, get_password_hash, create_refresh_token, decode_token
from app.crud import authorized_required
from app.dependencies import get_db
from app.exceptions import BadRequestException, DatabaseException
from app.models import User
from app.schemas.user_auth import Token, UserRegister

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Попытка входа пользователя: {form_data.username}")
        
        result = await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.username == form_data.username)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Пользователь не найден: {form_data.username}")
            raise BadRequestException("Неверное имя пользователя или пароль")

        if not verify_password(form_data.password, user.password):
            logger.warning(f"Неверный пароль для пользователя: {form_data.username}")
            raise BadRequestException("Неверное имя пользователя или пароль")

        token = create_access_token({"sub": str(user.id), "role": user.role.code})
        refresh_token = create_refresh_token({"sub": str(user.id), "role": user.role.code})
        logger.info(f"Успешный вход пользователя: {form_data.username}")
        return {"access_token": token, "refresh_token": refresh_token, "token_type": "bearer"}
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных при входе: {str(e)}")
        raise DatabaseException(f"Ошибка при аутентификации: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при входе: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Попытка регистрации пользователя: {user_data.username}")
        
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning(f"Пользователь уже существует: {user_data.username}")
            raise BadRequestException("Пользователь с таким именем пользователя уже зарегистрирован")

        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password=hashed_password,
            username=user_data.username,
            role_id=user_data.role_id
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Получаем роль пользователя
        role_code = None
        if new_user.role:
            role_code = new_user.role.code
        else:
            # Если роль не подгрузилась, делаем отдельный запрос
            result = await db.execute(select(User).options(selectinload(User.role)).where(User.id == new_user.id))
            user_with_role = result.scalar_one_or_none()
            if user_with_role and user_with_role.role:
                role_code = user_with_role.role.code

        token = create_access_token({"sub": str(new_user.id), "role": role_code})
        refresh_token = create_refresh_token({"sub": str(new_user.id), "role": role_code})
        logger.info(f"Успешная регистрация пользователя: {user_data.username}")
        return {"access_token": token, "refresh_token": refresh_token, "token_type": "bearer"}
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных при регистрации: {str(e)}")
        raise DatabaseException(f"Ошибка при регистрации пользователя: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при регистрации: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.get("/me")
async def get_me(user=Depends(authorized_required)):
    try:
        logger.info(f"Получение информации о пользователе: {user.username}")
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "role_id": user.role_id,
            "role_code": user.role.code,
            "role_name": user.role.name
        }
    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


from pydantic import BaseModel

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh" or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Недействительный refresh token")
    user_id = payload["sub"]
    role = payload.get("role")
    # На всякий случай можно получить роль из БД, если нужно
    access_token = create_access_token({"sub": str(user_id), "role": role})
    new_refresh_token = create_refresh_token({"sub": str(user_id), "role": role})
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
