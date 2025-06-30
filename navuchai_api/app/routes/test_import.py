from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import tempfile
import os
import logging
import io

from app.crud import test_import as crud
from app.dependencies import get_db
from app.exceptions import DatabaseException, BadRequestException, NotFoundException
from app.schemas.test_import import TestImportResponse
from app.crud import admin_moderator_required
from app.models import User
from app.utils.excel_parser import create_excel_template, create_full_friendly_excel_template

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/test-import", tags=["Test Import"])


@router.post("/excel/", response_model=TestImportResponse)
async def import_test_from_excel(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_moderator_required)
):
    temp_file_path = None
    try:
        logger.info(f"Начинаем импорт теста из Excel файла: {file.filename}")
        
        # Проверяем тип файла
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise BadRequestException("Поддерживаются только файлы Excel (.xlsx, .xls)")
        
        # Проверяем размер файла (максимум 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise BadRequestException("Размер файла не должен превышать 10MB")
        
        # Сохраняем файл во временную директорию
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Файл сохранен во временную директорию: {temp_file_path}")
        
        # Импортируем тест
        result = await crud.import_test_from_excel(db, temp_file_path, current_user.id)
        
        if result.success:
            logger.info(f"Тест успешно импортирован. ID: {result.test_id}, вопросов: {result.imported_questions}")
        else:
            logger.warning(f"Импорт завершен с ошибками: {result.message}")
        
        return result
        
    except (BadRequestException, DatabaseException, NotFoundException) as e:
        logger.error(f"Ошибка при импорте теста: {str(e)}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Неожиданная ошибка при импорте теста: {str(e)}")
        raise DatabaseException(f"Ошибка при импорте теста: {str(e)}")
    finally:
        # Удаляем временный файл только после завершения всех операций
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Временный файл удален: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Не удалось удалить временный файл {temp_file_path}: {str(e)}")


@router.get("/template/")
async def download_excel_template(
    current_user: User = Depends(admin_moderator_required)
):
    try:
        logger.info(f"Создание Excel шаблона для пользователя {current_user.id}")
        
        # Создаем Excel файл в памяти
        excel_buffer = io.BytesIO()
        create_full_friendly_excel_template(excel_buffer)
        excel_buffer.seek(0)
        
        logger.info("Excel шаблон успешно создан")
        
        return StreamingResponse(
            io.BytesIO(excel_buffer.getvalue()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=test_import_template.xlsx"}
        )
            
    except Exception as e:
        logger.error(f"Ошибка при создании шаблона: {str(e)}")
        raise DatabaseException(f"Ошибка при создании шаблона: {str(e)}") 