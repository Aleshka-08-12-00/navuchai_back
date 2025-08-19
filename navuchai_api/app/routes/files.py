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
from app.crud import root_admin_moderator_required, update_course_images, authorized_required
from app.exceptions import DatabaseException, NotFoundException
from app.schemas.file import FileUploadResponse, FileCreate, FileUploadWithMobileResponse
from app.crud import file as file_crud
from app.crud.file import get_file, delete_file
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
        current_user: User = Depends(authorized_required),
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
        current_user: User = Depends(authorized_required),
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
        
        # Определяем формат для сохранения
        original_format = image.format
        if original_format:
            image_format = original_format
        else:
            # Если формат не определен, определяем по расширению файла
            ext_lower = ext.lower()
            if ext_lower in ['.png', '.gif', '.webp']:
                image_format = ext_lower[1:].upper()  # Убираем точку и делаем заглавными
            else:
                image_format = 'JPEG'
        
        # Конвертируем в RGB только если действительно сохраняем как JPEG
        if image_format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA'):
            # Создаем белый фон для прозрачных областей
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        image.save(thumb_io, format=image_format)
        thumb_content = thumb_io.getvalue()
        # Определяем правильное расширение для thumbnail'а
        if image_format.upper() == 'PNG':
            thumb_ext = '.png'
        elif image_format.upper() == 'GIF':
            thumb_ext = '.gif'
        elif image_format.upper() == 'WEBP':
            thumb_ext = '.webp'
        else:
            thumb_ext = '.jpg'
        
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

        # Определяем правильный content_type для thumbnail'а
        if image_format.upper() == 'PNG':
            thumb_content_type = 'image/png'
        elif image_format.upper() == 'GIF':
            thumb_content_type = 'image/gif'
        elif image_format.upper() == 'WEBP':
            thumb_content_type = 'image/webp'
        else:
            thumb_content_type = 'image/jpeg'
        
        # Сохраняем уменьшенную копию в БД
        mobile_file_data = FileCreate(
            type=thumb_content_type,
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
        
        # Определяем формат для сохранения
        original_format = image.format
        if original_format:
            image_format = original_format
        else:
            # Если формат не определен, определяем по расширению файла
            ext_lower = ext.lower()
            if ext_lower in ['.png', '.gif', '.webp']:
                image_format = ext_lower[1:].upper()  # Убираем точку и делаем заглавными
            else:
                image_format = 'JPEG'
        
        # Конвертируем в RGB только если действительно сохраняем как JPEG
        if image_format.upper() == 'JPEG' and image.mode in ('RGBA', 'LA'):
            # Создаем белый фон для прозрачных областей
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        image.save(thumb_io, format=image_format)
        thumb_content = thumb_io.getvalue()
        # Определяем правильное расширение для thumbnail'а
        if image_format.upper() == 'PNG':
            thumb_ext = '.png'
        elif image_format.upper() == 'GIF':
            thumb_ext = '.gif'
        elif image_format.upper() == 'WEBP':
            thumb_ext = '.webp'
        else:
            thumb_ext = '.jpg'
        
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

        # Определяем правильный content_type для thumbnail'а
        if image_format.upper() == 'PNG':
            thumb_content_type = 'image/png'
        elif image_format.upper() == 'GIF':
            thumb_content_type = 'image/gif'
        elif image_format.upper() == 'WEBP':
            thumb_content_type = 'image/webp'
        else:
            thumb_content_type = 'image/jpeg'
        
        # Сохраняем уменьшенную копию в БД
        mobile_file_data = FileCreate(
            type=thumb_content_type,
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


@router.delete("/delete-avatar/", response_model=FileUploadWithMobileResponse)
async def delete_avatar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    try:
        user_result = await db.execute(select(User).where(User.id == current_user.id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise DatabaseException("Пользователь не найден")
        
        # Сохраняем ID текущих файлов аватара
        current_img_id = user.img_id
        current_thumbnail_id = user.thumbnail_id
        
        # Проверяем, что это не дефолтные аватары (174 и 175)
        files_to_delete = []
        if current_img_id not in [174, 175]:
            files_to_delete.append(current_img_id)
        if current_thumbnail_id not in [174, 175]:
            files_to_delete.append(current_thumbnail_id)
        
        # Сначала устанавливаем дефолтные аватары, чтобы избежать нарушения ограничений
        user.img_id = 174
        user.thumbnail_id = 175
        await db.commit()
        await db.refresh(user)
        
        # Теперь удаляем старые файлы из MinIO и записи из БД
        
        for file_id in files_to_delete:
            try:
                file_record = await get_file(db, file_id)
                
                # Извлекаем ключ файла из URL
                # URL имеет формат: https://minio.example.com/bucket-name/user_123/avatars/filename.ext
                file_url = file_record.path
                if MINIO_BUCKET_NAME in file_url:
                    # Извлекаем путь после bucket name
                    bucket_prefix = f"{MINIO_URL_SERT}/{MINIO_BUCKET_NAME}/"
                    if file_url.startswith(bucket_prefix):
                        file_key = file_url[len(bucket_prefix):]
                        
                        # Удаляем файл из MinIO
                        try:
                            s3.delete_object(Bucket=MINIO_BUCKET_NAME, Key=file_key)
                        except ClientError as e:
                            # Логируем ошибку, но продолжаем выполнение
                            print(f"Ошибка при удалении файла из MinIO: {str(e)}")
                
                # Удаляем запись из БД
                await delete_file(db, file_id)
                
            except Exception as e:
                # Логируем ошибку, но продолжаем выполнение
                print(f"Ошибка при удалении файла {file_id}: {str(e)}")
        
        # Делаем финальный commit для удаления файлов
        await db.commit()
        
        # Получаем информацию о дефолтных файлах
        original_file = await get_file(db, 174)
        mobile_file = await get_file(db, 175)
        
        # Формируем ответ в том же формате, что и при загрузке аватара
        original_response = FileUploadResponse(
            success=True,
            id=original_file.id,
            filename=original_file.name,
            content_type=original_file.type,
            size=original_file.size,
            url=original_file.path,
            uploaded_at=original_file.created_at,
            message="Дефолтный аватар установлен"
        )
        
        mobile_response = FileUploadResponse(
            success=True,
            id=mobile_file.id,
            filename=mobile_file.name,
            content_type=mobile_file.type,
            size=mobile_file.size,
            url=mobile_file.path,
            uploaded_at=mobile_file.created_at,
            message="Дефолтная миниатюра установлена"
        )
        
        return FileUploadWithMobileResponse(
            original=original_response,
            mobile=mobile_response
        )
    except (DatabaseException, NotFoundException) as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise DatabaseException(f"Ошибка при удалении аватарки: {str(e)}")
