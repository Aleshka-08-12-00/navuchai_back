from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from datetime import datetime
import uuid
import os
from PIL import Image
from io import BytesIO
from sqlalchemy import select

from app.dependencies import get_db
from app.models import User
from app.crud import admin_moderator_required, update_course_images, authorized_required
from app.exceptions import DatabaseException
from app.schemas.file import FileUploadResponse, FileCreate, FileUploadWithMobileResponse
from app.crud import file as file_crud
from app.config import (
    MINIO_URL,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET_NAME,
    MINIO_REGION,
    MINIO_URL_SERT
)

# Создание клиента
s3 = boto3.client(
    's3',
    endpoint_url=MINIO_URL,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name=MINIO_REGION
)

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post("/upload/", response_model=FileUploadResponse)
async def upload_file(
        file: UploadFile = File(...),
        current_user: User = Depends(admin_moderator_required),
        db: AsyncSession = Depends(get_db)
):
    try:
        content = await file.read()
        file_size = len(content)

        # Генерация уникального имени файла
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        # Загрузка файла в MinIO
        s3.put_object(
            Bucket=MINIO_BUCKET_NAME,
            Key=unique_filename,
            Body=content,
            ContentLength=file_size,
            ContentType=file.content_type
        )

        # Формирование URL для доступа к файлу
        file_url = f"{MINIO_URL_SERT}/{MINIO_BUCKET_NAME}/{unique_filename}"

        # Создание записи о файле в БД
        file_data = FileCreate(
            type=file.content_type,
            name=unique_filename,
            size=file_size,
            path=file_url,
            provider="minio",
            creator_id=current_user.id
        )
        db_file = await file_crud.create_file(db, file_data)

        return FileUploadResponse(
            id=db_file.id,
            filename=unique_filename,
            content_type=file.content_type,
            size=file_size,
            url=file_url,
            uploaded_at=datetime.now(),
            message="Файл успешно загружен"
        )
    except ClientError as e:
        raise DatabaseException(f"Ошибка при загрузке файла: {str(e)}")
    except Exception as e:
        raise DatabaseException(f"Неожиданная ошибка при загрузке файла: {str(e)}")


@router.post("/upload-image/", response_model=FileUploadWithMobileResponse)
async def upload_image(
        file: UploadFile = File(...),
        course_id: int | None = Query(default=None, alias="courseId"),
        current_user: User = Depends(admin_moderator_required),
        db: AsyncSession = Depends(get_db)
):
    try:
        content = await file.read()
        file_size = len(content)
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        user_folder = f"user_{current_user.id}"
        original_key = f"{user_folder}/images/{unique_filename}"
        mobile_key = f"{user_folder}/mobile_thumbnails/{unique_filename}"

        # Загрузка оригинала
        s3.put_object(
            Bucket=MINIO_BUCKET_NAME,
            Key=original_key,
            Body=content,
            ContentLength=file_size,
            ContentType=file.content_type
        )
        file_url = f"{MINIO_URL_SERT}/{MINIO_BUCKET_NAME}/{original_key}"

        # Создание уменьшенной копии
        image = Image.open(BytesIO(content))
        scale = 0.7
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        thumb_io = BytesIO()
        image_format = image.format if image.format else 'JPEG'
        # Если сохраняем как JPEG, конвертируем в RGB
        if image_format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA'):
            image = image.convert('RGB')
        image.save(thumb_io, format=image_format)
        thumb_content = thumb_io.getvalue()
        thumb_ext = ext if ext else '.jpg'
        thumb_filename = f"{uuid.uuid4().hex}{thumb_ext}"
        s3.put_object(
            Bucket=MINIO_BUCKET_NAME,
            Key=mobile_key,
            Body=thumb_content,
            ContentLength=len(thumb_content),
            ContentType=file.content_type
        )
        thumb_url = f"{MINIO_URL_SERT}/{MINIO_BUCKET_NAME}/{mobile_key}"

        # Сохраняем оригинал в БД
        file_data = FileCreate(
            type=file.content_type,
            name=unique_filename,
            size=file_size,
            path=file_url,
            provider="minio",
            creator_id=current_user.id
        )
        db_file = await file_crud.create_file(db, file_data)

        # Сохраняем уменьшенную копию в БД
        mobile_file_data = FileCreate(
            type=file.content_type,
            name=thumb_filename,
            size=len(thumb_content),
            path=thumb_url,
            provider="minio",
            creator_id=current_user.id
        )
        db_mobile_file = await file_crud.create_file(db, mobile_file_data)

        if course_id is not None:
            await update_course_images(db, course_id, db_file.id, db_mobile_file.id)

        original_response = FileUploadResponse(
            id=db_file.id,
            filename=unique_filename,
            content_type=file.content_type,
            size=file_size,
            url=file_url,
            uploaded_at=datetime.now(),
            message="Файл успешно загружен"
        )
        mobile_response = FileUploadResponse(
            id=db_mobile_file.id,
            filename=thumb_filename,
            content_type=file.content_type,
            size=len(thumb_content),
            url=thumb_url,
            uploaded_at=datetime.now(),
            message="Мобильная версия успешно загружена"
        )
        return FileUploadWithMobileResponse(
            original=original_response,
            mobile=mobile_response
        )
    except ClientError as e:
        raise DatabaseException(f"Ошибка при загрузке файла: {str(e)}")
    except Exception as e:
        raise DatabaseException(f"Неожиданная ошибка при загрузке файла: {str(e)}")


@router.post("/upload-avatar/", response_model=FileUploadWithMobileResponse)
async def upload_avatar(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        content = await file.read()
        file_size = len(content)
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{ext}"

        user_folder = f"user_{current_user.id}"
        original_key = f"{user_folder}/avatars/{unique_filename}"
        mobile_key = f"{user_folder}/avatar_thumbnails/{unique_filename}"

        # Загрузка оригинала
        s3.put_object(
            Bucket=MINIO_BUCKET_NAME,
            Key=original_key,
            Body=content,
            ContentLength=file_size,
            ContentType=file.content_type
        )
        file_url = f"{MINIO_URL_SERT}/{MINIO_BUCKET_NAME}/{original_key}"

        # Создание уменьшенной копии
        image = Image.open(BytesIO(content))
        scale = 0.7
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        thumb_io = BytesIO()
        image_format = image.format if image.format else 'JPEG'
        if image_format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA'):
            image = image.convert('RGB')
        image.save(thumb_io, format=image_format)
        thumb_content = thumb_io.getvalue()
        thumb_ext = ext if ext else '.jpg'
        thumb_filename = f"{uuid.uuid4().hex}{thumb_ext}"
        s3.put_object(
            Bucket=MINIO_BUCKET_NAME,
            Key=mobile_key,
            Body=thumb_content,
            ContentLength=len(thumb_content),
            ContentType=file.content_type
        )
        thumb_url = f"{MINIO_URL_SERT}/{MINIO_BUCKET_NAME}/{mobile_key}"

        # Сохраняем оригинал в БД
        file_data = FileCreate(
            type=file.content_type,
            name=unique_filename,
            size=file_size,
            path=file_url,
            provider="minio",
            creator_id=current_user.id
        )
        db_file = await file_crud.create_file(db, file_data)

        # Сохраняем уменьшенную копию в БД
        mobile_file_data = FileCreate(
            type=file.content_type,
            name=thumb_filename,
            size=len(thumb_content),
            path=thumb_url,
            provider="minio",
            creator_id=current_user.id
        )
        db_mobile_file = await file_crud.create_file(db, mobile_file_data)

        # Обновляем пользователя
        user_result = await db.execute(select(User).where(User.id == current_user.id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise DatabaseException("Пользователь не найден")
        user.img_id = db_file.id
        user.thumbnail_id = db_mobile_file.id
        await db.commit()
        await db.refresh(user)

        original_response = FileUploadResponse(
            id=db_file.id,
            filename=unique_filename,
            content_type=file.content_type,
            size=file_size,
            url=file_url,
            uploaded_at=datetime.now(),
            message="Аватар успешно загружен"
        )
        mobile_response = FileUploadResponse(
            id=db_mobile_file.id,
            filename=thumb_filename,
            content_type=file.content_type,
            size=len(thumb_content),
            url=thumb_url,
            uploaded_at=datetime.now(),
            message="Миниатюра успешно загружена"
        )
        return FileUploadWithMobileResponse(
            original=original_response,
            mobile=mobile_response
        )
    except ClientError as e:
        raise DatabaseException(f"Ошибка при загрузке файла: {str(e)}")
    except Exception as e:
        raise DatabaseException(f"Неожиданная ошибка при загрузке файла: {str(e)}")


@router.delete("/delete-avatar/", status_code=204)
async def delete_avatar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        user_result = await db.execute(select(User).where(User.id == current_user.id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise DatabaseException("Пользователь не найден")
        user.img_id = 174
        user.thumbnail_id = 175
        await db.commit()
        await db.refresh(user)
        return
    except Exception as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении аватарки: {str(e)}")
