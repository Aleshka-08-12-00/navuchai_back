from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from app.auth import verify_password, create_access_token, get_password_hash
from app.crud import authorized_required
from app.dependencies import get_db
from app.exceptions import BadRequestException, DatabaseException
from app.models import User
from app.schemas.user_auth import Token, UserRegister

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(User).where(User.username == form_data.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(form_data.password, user.password):
            raise BadRequestException("Неверное имя пользователя или пароль")

        token = create_access_token({"sub": str(user.id)})
        return {"access_token": token}
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при аутентификации")


@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(User).where(User.name == user_data.name)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise BadRequestException("Пользователь с таким именем уже зарегистрирован")

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

        token = create_access_token({"sub": str(new_user.id)})
        return {"access_token": token}
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при регистрации пользователя")


@router.get("/me")
async def get_me(user=Depends(authorized_required)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "name": user.name,
        "role_id": user.role_id,
        "role_code": user.role.code,
        "role_name": user.role.name
    }
