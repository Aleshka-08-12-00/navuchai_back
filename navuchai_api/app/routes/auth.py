from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import logging
import csv
import io
from datetime import datetime

from app.auth import verify_password, create_access_token, get_password_hash, create_refresh_token, decode_token
from app.crud import authorized_required
from app.dependencies import get_db
from app.exceptions import BadRequestException, DatabaseException, NotFoundException
from app.models import User
from app.crud.user_group import add_group_member, get_group, import_users_from_csv
from app.schemas.user_auth import Token, UserRegister, UserRegisterWithGroup, UserImportResponse

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


def create_user_from_data(user_data):
    """Вспомогательная функция для создания пользователя с правильной обработкой img_id"""
    hashed_password = get_password_hash(user_data.password)
    
    # Подготавливаем данные пользователя, исключая None значения для img_id
    user_data_dict = {
        'name': user_data.name,
        'email': user_data.email,
        'password': hashed_password,
        'username': user_data.username,
        'role_id': user_data.role_id,
        'organization_id': user_data.organization_id,
        'position_id': user_data.position_id,
        'department_id': user_data.department_id,
        'phone_number': user_data.phone_number
    }
    
    # Добавляем img_id только если оно не None
    if user_data.img_id is not None:
        user_data_dict['img_id'] = user_data.img_id
    
    return User(**user_data_dict)


@router.post("/login/", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Попытка входа пользователя: {form_data.username}")
        # Сначала ищем по username
        result = await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.username == form_data.username)
        )
        user = result.scalar_one_or_none()
        # Если не найдено — ищем по email
        if not user:
            result = await db.execute(
                select(User)
                .options(selectinload(User.role))
                .where(User.email == form_data.username)
            )
            user = result.scalar_one_or_none()
        if not user or not verify_password(form_data.password, user.password):
            logger.warning(f"Ошибка входа: пользователь не найден или неверный пароль: {form_data.username}")
            raise BadRequestException("Неверное имя пользователя/email или пароль")
        token = create_access_token({
            "sub": str(user.id),
            "role": user.role.code,
            "username": user.username,
            "email": user.email
        })
        refresh_token = create_refresh_token({
            "sub": str(user.id),
            "role": user.role.code,
            "username": user.username,
            "email": user.email
        })
        logger.info(f"Успешный вход пользователя: {form_data.username}")
        return {"access_token": token, "refresh_token": refresh_token, "token_type": "bearer"}
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных при входе: {str(e)}")
        raise DatabaseException("Ошибка при аутентификации пользователя")


@router.post("/register/", response_model=Token)
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

        new_user = create_user_from_data(user_data)

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

        token = create_access_token({
            "sub": str(new_user.id),
            "role": role_code,
            "username": new_user.username,
            "email": new_user.email
        })
        refresh_token = create_refresh_token({
            "sub": str(new_user.id),
            "role": role_code,
            "username": new_user.username,
            "email": new_user.email
        })
        logger.info(f"Успешная регистрация пользователя: {user_data.username}")
        return {"access_token": token, "refresh_token": refresh_token, "token_type": "bearer"}
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных при регистрации: {str(e)}")
        raise DatabaseException(f"Ошибка при регистрации пользователя: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при регистрации: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.post("/register-with-group/", response_model=Token)
async def register_with_group(user_data: UserRegisterWithGroup, db: AsyncSession = Depends(get_db)):
    try:
        logger.info(f"Попытка регистрации пользователя с группой: {user_data.username}, группа: {user_data.group_id}")

        # Проверяем существование группы
        try:
            await get_group(db, user_data.group_id)
        except NotFoundException:
            logger.warning(f"Группа не найдена: {user_data.group_id}")
            raise BadRequestException("Указанная группа не найдена")

        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            logger.warning(f"Пользователь уже существует: {user_data.username}")
            raise BadRequestException("Пользователь с таким именем пользователя уже зарегистрирован")

        new_user = create_user_from_data(user_data)

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Добавляем пользователя в группу
        try:
            await add_group_member(db, user_data.group_id, new_user.id)
            logger.info(f"Пользователь {new_user.username} успешно добавлен в группу {user_data.group_id}")
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя в группу: {str(e)}")
            # Не откатываем создание пользователя, только логируем ошибку
            # Пользователь уже создан, но не добавлен в группу

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

        token = create_access_token({
            "sub": str(new_user.id),
            "role": role_code,
            "username": new_user.username,
            "email": new_user.email
        })
        refresh_token = create_refresh_token({
            "sub": str(new_user.id),
            "role": role_code,
            "username": new_user.username,
            "email": new_user.email
        })
        logger.info(f"Успешная регистрация пользователя с группой: {user_data.username}")
        return {"access_token": token, "refresh_token": refresh_token, "token_type": "bearer"}
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных при регистрации с группой: {str(e)}")
        raise DatabaseException(f"Ошибка при регистрации пользователя: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при регистрации с группой: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.get("/me/")
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


@router.post("/refresh/", response_model=Token)
async def refresh_token_endpoint(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh" or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Недействительный refresh token")
    user_id = payload["sub"]
    role = payload.get("role")
    username = payload.get("username")
    email = payload.get("email")
    # На всякий случай можно получить роль из БД, если нужно
    access_token = create_access_token({
        "sub": str(user_id),
        "role": role,
        "username": username,
        "email": email
    })
    new_refresh_token = create_refresh_token({
        "sub": str(user_id),
        "role": role,
        "username": username,
        "email": email
    })
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}


@router.post("/import-users-csv/", response_model=UserImportResponse)
async def import_users_from_csv_endpoint(
    file: UploadFile = File(...),
    group_id: int = Form(...),
    default_role_id: int = Form(default=3),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    """
    Импортирует пользователей из CSV файла и добавляет их в группу
    
    CSV должен содержать колонки: email, name
    Колонка password опциональна - если не указана, используется "1234"
    """
    try:
        logger.info(f"Начинаем импорт пользователей из CSV: {file.filename}, группа: {group_id}")
        
        # Проверяем тип файла
        if not file.filename or not file.filename.endswith('.csv'):
            raise BadRequestException("Поддерживаются только CSV файлы (.csv)")
        
        # Проверяем размер файла (максимум 5MB)
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:  # 5MB
            raise BadRequestException("Размер файла не должен превышать 5MB")
        
        # Декодируем содержимое
        try:
            csv_content = content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                csv_content = content.decode('cp1251')  # Попробуем Windows-1251
            except UnicodeDecodeError:
                raise BadRequestException("Не удалось декодировать файл. Используйте UTF-8 или Windows-1251")
        
        # Импортируем пользователей
        result = await import_users_from_csv(db, csv_content, group_id, default_role_id)
        
        logger.info(f"Импорт завершен. Обработано: {result.total_processed}, "
                   f"создано: {result.created}, добавлено в группу: {result.added_to_group}, "
                   f"уже в группе: {result.already_in_group}, ошибок: {result.errors}")
        
        return result
        
    except (BadRequestException, DatabaseException, NotFoundException) as e:
        logger.error(f"Ошибка при импорте пользователей: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Неожиданная ошибка при импорте пользователей: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.get("/download-csv-template/")
async def download_csv_template():
    """
    Скачивает пример CSV файла для импорта пользователей
    """
    try:
        # Создаем содержимое CSV файла
        csv_content = """email,name,password
ivan.ivanov@example.com,Иван Иванов,password123
maria.petrova@example.com,Мария Петрова,
alex.sidorov@example.com,Алексей Сидоров,secret456
elena.kuznetsova@example.com,Елена Кузнецова,
dmitry.volkov@example.com,Дмитрий Волков,volkov789"""
        
        # Создаем поток для ответа
        def generate_csv():
            yield csv_content.encode('utf-8')
        
        return StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=users_template.csv"
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка при создании CSV шаблона: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")
