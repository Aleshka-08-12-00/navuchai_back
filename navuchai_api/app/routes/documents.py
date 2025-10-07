from typing import Optional
from datetime import datetime
import os
import uuid
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.crud import authorized_required, get_current_user, root_admin_moderator_required
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse, DocumentUploadResponse
from app.schemas.file import FileUploadResponse, FileCreate
from app.crud.document import list_documents, get_document, create_document, update_document, delete_document
from app.crud.folder import get_folder_shallow
from app.crud import file as file_crud
from app.exceptions import NotFoundException, DatabaseException
from app.config import MINIO_URL, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME, MINIO_REGION, MINIO_URL_SERT
from app.models import User
import re
import urllib.parse
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/documents", tags=["Documents"])

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_URL,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name=MINIO_REGION,
)

def _extract_key(url: str) -> str | None:
    prefix = f"{MINIO_URL_SERT}/{MINIO_BUCKET_NAME}/"
    if url.startswith(prefix):
        return url[len(prefix):]
    return None

@router.get("/", response_model=list[DocumentResponse], dependencies=[Depends(authorized_required)])
async def list_route(db: AsyncSession = Depends(get_db), folder_id: Optional[int] = Query(default=None, alias="folderId"), q: Optional[str] = None, type: Optional[str] = None, skip: int = 0, limit: int = Query(50, le=200)):
    return await list_documents(db, folder_id, q, type, skip, limit)

@router.get("/{doc_id}/", response_model=DocumentResponse, dependencies=[Depends(authorized_required)])
async def read_route(doc_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await get_document(db, doc_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(root_admin_moderator_required)])
async def create_route(data: DocumentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await create_document(db, user.id, data.type, data.name, data.size, data.path, data.provider, data.folder_id)

@router.put("/{doc_id}/", response_model=DocumentResponse, dependencies=[Depends(root_admin_moderator_required)])
async def update_route(doc_id: int, data: DocumentUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await update_document(db, doc_id, data.type, data.name, data.size, data.path, data.provider, data.folder_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{doc_id}/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(root_admin_moderator_required)])
async def delete_route(doc_id: int, db: AsyncSession = Depends(get_db)):
    try:
        doc = await get_document(db, doc_id)
        key = _extract_key(doc.path)
        if key:
            try:
                s3.delete_object(Bucket=MINIO_BUCKET_NAME, Key=key)
            except ClientError as e:
                raise DatabaseException(f"Ошибка при удалении из MinIO: {str(e)}")
        await delete_document(db, doc_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/upload/", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(root_admin_moderator_required)])
async def upload_document(
    file: UploadFile = File(...),
    folder_id: int = Query(..., alias="folderId"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        # Проверяем, что папка существует
        folder = await get_folder_shallow(db, folder_id)
        if not folder:
            raise NotFoundException("Папка не найдена")
        content = await file.read()
        size = len(content)
        ext = os.path.splitext(file.filename)[1]
        key = f"user_{user.id}/docs/{uuid.uuid4().hex}{ext}"
        s3.put_object(
            Bucket=MINIO_BUCKET_NAME,
            Key=key,
            Body=content,
            ContentLength=size,
            ContentType=file.content_type
        )
        url = f"{MINIO_URL_SERT}/{MINIO_BUCKET_NAME}/{key}"
        file_row = await file_crud.create_file(
            db,
            FileCreate(
                type=file.content_type,
                name=os.path.basename(key),
                size=size,
                path=url,
                provider="minio",
                creator_id=user.id
            )
        )
        # Привязываем документ к папке
        doc = await create_document(
            db,
            user.id,
            file.content_type,
            file.filename,
            size,
            url,
            "minio",
            folder_id
        )
        return DocumentUploadResponse(
            document=DocumentResponse.model_validate(doc, from_attributes=True),
            file=FileUploadResponse(
                id=file_row.id,
                filename=os.path.basename(key),
                content_type=file.content_type,
                size=size,
                url=url,
                uploaded_at=datetime.now(),
                message="Файл успешно загружен"
            ),
        )
    except ClientError as e:
        raise DatabaseException(f"Ошибка при загрузке файла: {str(e)}")
    except (DatabaseException, NotFoundException) as e:
        raise HTTPException(status_code=400, detail=str(e))

def _content_disposition(name: str) -> str:
    fallback = re.sub(r'[^A-Za-z0-9._-]+', '_', name or 'file')
    encoded = urllib.parse.quote(name, encoding='utf-8')
    return f"attachment; filename={fallback}; filename*=UTF-8''{encoded}"

@router.get("/{doc_id}/download-url/", dependencies=[Depends(authorized_required)])
async def download_proxy(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await get_document(db, doc_id)
    key = _extract_key(doc.path)
    if not key:
        raise DatabaseException("Неверный путь к объекту")

    obj = s3.get_object(Bucket=MINIO_BUCKET_NAME, Key=key)
    body = obj["Body"]

    def _iter():
        while True:
            chunk = body.read(1024 * 1024)
            if not chunk:
                break
            yield chunk

    headers = {
        "Content-Disposition": _content_disposition(doc.name),
        "Cache-Control": "no-store",
    }

    return StreamingResponse(_iter(), headers=headers, media_type=(doc.type or "application/octet-stream"))
