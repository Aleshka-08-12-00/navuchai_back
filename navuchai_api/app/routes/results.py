from datetime import datetime
from io import BytesIO
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import authorized_required, get_analytics_data_by_view, get_column_mapping, get_sheet_name, get_filename
from app.crud import result as result_crud
from app.crud.analytics import get_analytics_user_test_question_performance
from app.crud.result import get_result, get_result_answers
from app.dependencies import get_db
from app.exceptions import NotFoundException, DatabaseException, ForbiddenException
from app.models import User, UserAnswer
from app.schemas.result import ResultCreate, ResultResponse, UserAnswerResponse
from app.utils import convert_result
from app.utils.excel_parser import generate_analytics_excel
from app.utils.formatters import apply_excel_formatting
from app.utils.report_generator import generate_result_excel, transliterate_cyrillic
from pydantic import BaseModel

router = APIRouter(prefix="/api/results", tags=["Results"])


def convert_user_answer(answer: UserAnswer) -> UserAnswerResponse:
    """Преобразует модель UserAnswer в схему UserAnswerResponse"""
    return UserAnswerResponse(
        id=answer.id,
        result_id=answer.result_id,
        question_id=answer.question_id,
        user_id=answer.user_id,
        answer=answer.answer,
        created_at=answer.created_at,
        updated_at=answer.updated_at
    )


def clean_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Очищает datetime колонки от часовых поясов для совместимости с Excel"""
    for column in df.columns:
        if df[column].dtype == 'object':
            # Проверяем, содержит ли колонка datetime объекты
            sample_values = df[column].dropna().head(10)
            if len(sample_values) > 0 and any(isinstance(val, datetime) for val in sample_values):
                # Убираем часовые пояса из datetime объектов
                df[column] = df[column].apply(
                    lambda x: x.replace(tzinfo=None) if isinstance(x, datetime) and x.tzinfo else x
                )
    return df


@router.get("/excel/")
async def export_results_excel(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        # Получаем аналитические данные из представления analytics_user_performance
        analytics_data = await get_analytics_data_by_view(db, 'analytics_user_performance')
        
        # Создаем DataFrame из аналитических данных
        df = pd.DataFrame(analytics_data)
        
        # Очищаем datetime колонки от часовых поясов
        df = clean_datetime_columns(df)
        
        # Получаем маппинг колонок для переименования
        column_mapping = get_column_mapping('analytics_user_performance')
        
        # Переименовываем колонки для лучшей читаемости в Excel
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Принудительно приводим все потенциально числовые колонки к float, кроме дат и времени
        numeric_keywords = [
            'процент', 'percent', 'балл', 'score', 'total', 'всего', 'дней', 'попыт', 'attempt',
            'актив', 'active', 'заверш', 'complete', 'доступ', 'access', 'правиль', 'correct',
            'неправиль', 'incorrect', 'отклонение', 'stddev', 'минималь', 'min', 'максималь', 'max'
        ]
        exclude_keywords = ['дата', 'date', 'время', 'time']
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in numeric_keywords) and not any(ex in col_lower for ex in exclude_keywords):
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Применяем форматирование для Excel (округляем до сотых, заменяем 0E-20 на 0)
        df = apply_excel_formatting(df)
        
        # Создаем Excel файл
        output = BytesIO()
        sheet_name = get_sheet_name('analytics_user_performance')
        filename = get_filename('analytics_user_performance')
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Получаем рабочий лист для форматирования
            worksheet = writer.sheets[sheet_name]
            
            # Автоматически подгоняем ширину колонок
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Ограничиваем максимальную ширину
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при экспорте аналитических данных в Excel")


@router.get("/excel/{view_name}/")
async def export_analytics_excel(
        view_name: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    """Экспорт данных из любого аналитического представления в Excel, включая pivot-отчёт по пользователям и тестам"""
    try:
        if view_name == "analytics_user_test_question_performance":
            # Специальная логика для pivot-отчёта
            analytics_data = await get_analytics_user_test_question_performance(db)
            output = generate_analytics_excel(analytics_data)
            filename = 'user_tests_report.xlsx'
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        # --- Универсальная логика для остальных view ---
        analytics_data = await get_analytics_data_by_view(db, view_name)
        df = pd.DataFrame(analytics_data)
        df = clean_datetime_columns(df)
        column_mapping = get_column_mapping(view_name)
        if column_mapping:
            df = df.rename(columns=column_mapping)
        numeric_keywords = [
            'процент', 'percent', 'балл', 'score', 'total', 'всего', 'дней', 'попыт', 'attempt',
            'актив', 'active', 'заверш', 'complete', 'доступ', 'access', 'правиль', 'correct',
            'неправиль', 'incorrect', 'отклонение', 'stddev', 'минималь', 'min', 'максималь', 'max'
        ]
        exclude_keywords = ['дата', 'date', 'время', 'time']
        for col in df.columns:
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in numeric_keywords) and not any(ex in col_lower for ex in exclude_keywords):
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = apply_excel_formatting(df)
        output = BytesIO()
        sheet_name = get_sheet_name(view_name)
        filename = get_filename(view_name)
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except SQLAlchemyError:
        raise DatabaseException(f"Ошибка при экспорте данных из представления {view_name}")


@router.post("/", response_model=ResultResponse)
async def create_test_result(
        result: ResultCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        if result.user_id != current_user.id:
            raise ForbiddenException("Нельзя создать результат для другого пользователя")
        created_result = await result_crud.create_result(db, result)
        return await convert_result(created_result, current_user, db)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при сохранении результата")


@router.get("/{result_id}/", response_model=ResultResponse)
async def get_result_by_id(
        result_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        result = await result_crud.get_result(db, result_id)
        if current_user.role.code not in ["admin", "moderator"] and result.user_id != current_user.id:
            raise ForbiddenException("Нет доступа к этому результату")
        return await convert_result(result, current_user, db)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении результата")


@router.get("/user/{user_id}/", response_model=List[ResultResponse])
async def get_user_results(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        if current_user.role.code not in ["admin", "moderator"] and user_id != current_user.id:
            raise ForbiddenException("Нет доступа к результатам другого пользователя")
        results = await result_crud.get_user_results(db, user_id)
        return [await convert_result(result, current_user, db) for result in results]
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении результатов пользователя")


@router.get("/test/{test_id}/", response_model=List[ResultResponse])
async def get_test_results(
        test_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        results = await result_crud.get_test_results(db, test_id)
        return [await convert_result(result, current_user, db) for result in results]
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении результатов теста")


@router.get("/", response_model=List[ResultResponse])
async def get_all_results(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        if current_user.role.code in ["admin", "moderator"]:
            results = await result_crud.get_all_results(db)
        else:
            results = await result_crud.get_user_results(db, current_user.id)
        return [await convert_result(result, current_user, db) for result in results]
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка результатов")


@router.get("/{result_id}/export/")
async def export_result(
    result_id: int,
    current_user: User = Depends(authorized_required),
    db: AsyncSession = Depends(get_db)
):
    """Экспорт результата теста только в Excel формате (без параметра format)"""
    try:
        result = await get_result(db, result_id)
        # Проверяем права доступа
        if current_user.role.code != "admin" and result.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Нет доступа к этому результату")
        answers = await get_result_answers(db, result_id)
        safe_name = transliterate_cyrillic(result.user.name or 'unknown')
        filename = f"result_{result_id}_{safe_name}_{result.created_at.strftime('%Y%m%d_%H%M%S')}.xlsx"
        output = generate_result_excel(result, answers)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=str(e))


class FinalizeResultBody(BaseModel):
    result_id: int

@router.post("/finalize/", response_model=ResultResponse)
async def finalize_result_after_manual_check(
    body: FinalizeResultBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    if current_user.role.code not in ["admin", "moderator"]:
        raise ForbiddenException("Нет прав для финализации результата после ручной проверки")
    from app.crud.result import finalize_manual_check_result
    result = await finalize_manual_check_result(db, body.result_id)
    return await convert_result(result, current_user, db)


class ManualCheckBody(BaseModel):
    result_id: int
    question_id: int
    is_correct: bool

@router.post("/manual_check/", response_model=ResultResponse)
async def manual_check_answer(
    body: ManualCheckBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized_required)
):
    if current_user.role.code not in ["admin", "moderator"]:
        raise ForbiddenException("Нет прав для ручной проверки ответа")
    from app.crud.result import get_result
    result_obj = await get_result(db, body.result_id)
    checked_answers = result_obj.result.get("checked_answers", [])
    updated = False
    for ans in checked_answers:
        if ans.get("question_id") == body.question_id:
            ans["is_correct"] = body.is_correct
            if "check_details" in ans and isinstance(ans["check_details"], dict):
                ans["check_details"]["message"] = "Вопрос проверен модератором"
            updated = True
            break
    if not updated:
        raise NotFoundException(f"Вопрос с ID {body.question_id} не найден в результате {body.result_id}")
    result_obj.result["checked_answers"] = checked_answers
    from sqlalchemy.ext.mutable import MutableDict
    if not isinstance(result_obj.result, MutableDict):
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy.ext.mutable import MutableDict
        result_obj.result = MutableDict(result_obj.result)
    await db.commit()
    await db.refresh(result_obj)
    return await convert_result(result_obj, current_user, db)
