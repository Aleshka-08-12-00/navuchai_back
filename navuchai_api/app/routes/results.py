from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import List
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO
from datetime import datetime
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import re

from app.crud import result as result_crud
from app.crud import authorized_required, get_analytics_data_by_view, get_column_mapping, get_sheet_name, get_filename
from app.dependencies import get_db
from app.exceptions import NotFoundException, DatabaseException, ForbiddenException
from app.models import User, Result, UserAnswer
from app.schemas.result import ResultCreate, ResultResponse, UserAnswerResponse
from app.utils import convert_result
from app.utils.formatters import apply_excel_formatting
from app.crud.analytics import get_analytics_user_test_question_performance
from app.utils.excel_parser import generate_analytics_excel

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
        # Проверяем, что пользователь создает результат для себя
        if result.user_id != current_user.id:
            raise ForbiddenException("Нельзя создать результат для другого пользователя")

        created_result = await result_crud.create_result(db, result)
        return convert_result(created_result)
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
        # Если не админ или модератор — проверяем, что пользователь запрашивает свой результат
        if current_user.role.code not in ["admin", "moderator"] and result.user_id != current_user.id:
            raise ForbiddenException("Нет доступа к этому результату")
        return convert_result(result)
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении результата")


@router.get("/user/{user_id}/", response_model=List[ResultResponse])
async def get_user_results(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(authorized_required)
):
    try:
        # Если не админ или модератор — проверяем, что пользователь запрашивает свои результаты
        if current_user.role.code not in ["admin", "moderator"] and user_id != current_user.id:
            raise ForbiddenException("Нет доступа к результатам другого пользователя")
        results = await result_crud.get_user_results(db, user_id)
        return [convert_result(result) for result in results]
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
        return [convert_result(result) for result in results]
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
        return [convert_result(result) for result in results]
    except SQLAlchemyError:
        raise DatabaseException("Ошибка при получении списка результатов")
