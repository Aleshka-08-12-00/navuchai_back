from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from datetime import datetime

from app.dependencies import get_db
from app.models import User
from app.crud import admin_teacher_required
from app.exceptions import DatabaseException
from app.schemas.file import FileUploadResponse
from app.config import (
    MINIO_URL,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    MINIO_BUCKET_NAME,
    MINIO_REGION
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
        current_user: User = Depends(admin_teacher_required),
        db: AsyncSession = Depends(get_db)
):

    try:
        content = await file.read()
        file_size = len(content)
        
        # Загрузка файла в MinIO
        s3.put_object(
            Bucket=MINIO_BUCKET_NAME,
            Key=file.filename,
            Body=content,
            ContentLength=file_size,
            ContentType=file.content_type
        )
        
        # Формирование URL для доступа к файлу
        file_url = f"{MINIO_URL}/{MINIO_BUCKET_NAME}/{file.filename}"
        
        return FileUploadResponse(
            filename=file.filename,
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
