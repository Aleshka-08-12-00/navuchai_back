from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from typing import List, Dict, Any
from datetime import datetime
from app.exceptions import DatabaseException
from app.utils.formatters import format_numeric_value
from app.models.analytics_views import AnalyticsView
from sqlalchemy.future import select


async def get_analytics_user_performance(db: AsyncSession) -> List[Dict[str, Any]]:
    """Получение данных из представления analytics_user_performance"""
    try:
        # Выполняем запрос к представлению
        stmt = text("""
        SELECT 
            user_id,
            user_name,
            user_email,
            role_name,
            total_tests_accessed,
            total_tests_completed,
            avg_score,
            best_score,
            worst_score,
            total_attempts,
            avg_percent_completion,
            total_questions_answered,
            first_test_date,
            last_test_date,
            days_active
        FROM analytics_user_performance
        ORDER BY user_name
        """)
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        # Преобразуем результаты в список словарей
        analytics_data = []
        for row in rows:
            # Обрабатываем datetime поля - убираем часовые пояса
            first_test_date = row[12]
            if isinstance(first_test_date, datetime) and first_test_date and first_test_date.tzinfo:
                first_test_date = first_test_date.replace(tzinfo=None)
                
            last_test_date = row[13]
            if isinstance(last_test_date, datetime) and last_test_date and last_test_date.tzinfo:
                last_test_date = last_test_date.replace(tzinfo=None)
            
            analytics_data.append({
                "user_id": row[0],
                "user_name": row[1],
                "user_email": row[2],
                "role_name": row[3],
                "total_tests_accessed": row[4] or 0,
                "total_tests_completed": row[5] or 0,
                "avg_score": format_numeric_value(row[6]) if row[6] is not None else 0.0,
                "best_score": row[7] or 0,
                "worst_score": row[8] or 0,
                "total_attempts": row[9] or 0,
                "avg_percent_completion": format_numeric_value(row[10]) if row[10] is not None else 0.0,
                "total_questions_answered": row[11] or 0,
                "first_test_date": first_test_date,
                "last_test_date": last_test_date,
                "days_active": row[14] or 0
            })
        
        return analytics_data
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении аналитических данных: {str(e)}")




async def get_analytics_data_by_view(db: AsyncSession, view_name: str) -> List[Dict[str, Any]]:
    """Универсальный метод для получения данных из любого аналитического представления"""
    try:
        # Проверяем, что представление существует и безопасно
        allowed_views = [
            'analytics_user_performance',
            'analytics_user_performance_extended',
            'analytics_test_statistics',
            'analytics_group_performance',
            'analytics_question_analysis',
            'analytics_category_performance',
            # Здесь можно добавить другие представления в будущем
            # 'analytics_test_performance',
        ]
        
        if view_name not in allowed_views:
            raise DatabaseException(f"Представление {view_name} не разрешено для экспорта")
        
        # Выполняем запрос к представлению
        stmt = text(f"SELECT * FROM {view_name}")
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        # Получаем названия колонок
        columns = result.keys()
        
        # Преобразуем результаты в список словарей
        analytics_data = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                # Обрабатываем datetime значения - убираем часовые пояса
                if isinstance(value, datetime):
                    if value.tzinfo is not None:
                        value = value.replace(tzinfo=None)
                    row_dict[column] = value
                # Применяем форматирование к числовым значениям
                elif isinstance(value, (int, float)) and value is not None:
                    row_dict[column] = format_numeric_value(value)
                elif value is None:
                    row_dict[column] = 0 if column.startswith(('total_', 'avg_', 'best_', 'worst_', 'days_')) else None
                else:
                    row_dict[column] = value
            analytics_data.append(row_dict)
        
        return analytics_data
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении данных из представления {view_name}: {str(e)}")


def get_column_mapping(view_name: str) -> Dict[str, str]:
    """Возвращает маппинг колонок для переименования в Excel"""
    mappings = {
        'analytics_user_performance': {
            "user_id": "ID пользователя",
            "user_name": "Имя пользователя",
            "user_email": "Email",
            "role_name": "Роль",
            "total_tests_accessed": "Всего доступных тестов",
            "total_tests_completed": "Всего завершенных тестов",
            "avg_score": "Средний балл",
            "best_score": "Лучший балл",
            "worst_score": "Худший балл",
            "total_attempts": "Всего попыток",
            "avg_percent_completion": "Средний процент выполнения",
            "total_questions_answered": "Всего отвеченных вопросов",
            "first_test_date": "Дата первого теста",
            "last_test_date": "Дата последнего теста",
            "days_active": "Дней активности"
        },
        'analytics_user_performance_extended': {
            "user_id": "ID пользователя",
            "user_name": "Имя пользователя",
            "user_email": "Email",
            "role_name": "Роль",
            "total_tests_accessed": "Всего доступных тестов",
            "total_tests_completed": "Всего завершенных тестов",
            "avg_score": "Средний балл",
            "best_score": "Лучший балл",
            "worst_score": "Худший балл",
            "total_attempts": "Всего попыток",
            "avg_percent_completion": "Средний процент выполнения",
            "total_questions_answered": "Всего отвеченных вопросов",
            "first_test_date": "Дата первого теста",
            "last_test_date": "Дата последнего теста",
            "days_active": "Дней активности",
            "best_time_test_title": "Название теста с лучшим временем",
            "best_time_seconds": "Лучшее время (сек)",
            "best_time_score": "Балл за лучший тест по времени",
            "best_time_date": "Дата лучшего времени",
            "worst_time_test_title": "Название теста с худшим временем",
            "worst_time_seconds": "Худшее время (сек)",
            "worst_time_score": "Балл за худший тест по времени",
            "worst_time_date": "Дата худшего времени"
        },
        'analytics_test_statistics': {
            "test_id": "ID теста",
            "test_title": "Название теста",
            "test_description": "Описание теста",
            "category_name": "Категория",
            "creator_name": "Создатель",
            "time_limit": "Лимит времени (сек)",
            "locale_name": "Язык",
            "total_users_accessed": "Всего пользователей с доступом",
            "total_users_completed": "Всего пользователей завершивших",
            "total_attempts": "Всего попыток",
            "avg_score": "Средний балл",
            "min_score": "Минимальный балл",
            "max_score": "Максимальный балл",
            "score_stddev": "Стандартное отклонение балла",
            "avg_percent_completion": "Средний процент выполнения",
            "avg_completion_percent": "Средний процент завершения",
            "total_questions": "Всего вопросов",
            "completion_rate": "Процент завершения",
            "test_created_at": "Дата создания теста",
            "created_at": "Дата создания",
            "updated_at": "Дата обновления",
            "users_last_30_days": "Пользователей за 30 дней",
            "users_last_7_days": "Пользователей за 7 дней"
        },
        'analytics_group_performance': {
            "group_id": "ID группы",
            "group_name": "Название группы",
            "group_description": "Описание группы",
            "group_creator": "Создатель группы",
            "total_members": "Всего участников",
            "total_tests_accessed": "Всего доступных тестов",
            "total_tests_completed": "Всего завершенных тестов",
            "group_avg_score": "Средний балл группы",
            "group_best_score": "Лучший балл группы",
            "group_worst_score": "Худший балл группы",
            "group_avg_completion": "Средний процент выполнения группы",
            "total_group_attempts": "Всего попыток группы",
            "active_members": "Активных участников",
            "group_created_at": "Дата создания группы",
            "created_at": "Дата создания группы",
            "updated_at": "Дата обновления группы",
            "last_activity_date": "Дата последней активности"
        },
        'analytics_question_analysis': {
            "question_id": "ID вопроса",
            "question_text": "Текст вопроса",
            "question_type": "Тип вопроса",
            "used_in_tests": "Используется в тестах",
            "total_users_answered": "Всего пользователей ответило",
            "total_answers": "Всего ответов",
            "answer_rate": "Процент ответов",
            "correct_answer_rate": "Процент правильных ответов",
            "question_created_at": "Дата создания вопроса",
            "users_last_30_days": "Пользователей за 30 дней",
            "users_last_7_days": "Пользователей за 7 дней"
        },
        'analytics_category_performance': {
            "category_id": "ID категории",
            "category_name": "Название категории",
            "total_tests": "Всего тестов",
            "total_users_accessed": "Пользователей с доступом",
            "total_users_completed": "Пользователей завершивших",
            "total_attempts": "Всего попыток",
            "category_avg_score": "Средний балл по категории",
            "category_min_score": "Минимальный балл по категории",
            "category_max_score": "Максимальный балл по категории",
            "category_avg_completion": "Средний процент завершения по категории",
            "total_questions_in_category": "Всего вопросов в категории",
            "active_users_last_30_days": "Активных пользователей за 30 дней",
            "active_users_last_7_days": "Активных пользователей за 7 дней",
            "completion_rate_percent": "Процент завершения (%)"
        }
        # Здесь можно добавить маппинги для других представлений
    }
    
    return mappings.get(view_name, {})


def get_sheet_name(view_name: str) -> str:
    """Возвращает название листа для Excel"""
    sheet_names = {
        'analytics_user_performance': 'Аналитика производительности пользователей',
        'analytics_user_performance_extended': 'Расширенная аналитика производительности пользователей',
        'analytics_test_statistics': 'Статистика по тестам',
        'analytics_group_performance': 'Производительность групп',
        'analytics_question_analysis': 'Анализ вопросов',
        # Здесь можно добавить названия для других представлений
    }
    
    return sheet_names.get(view_name, 'Аналитические данные')


def get_filename(view_name: str) -> str:
    """Возвращает имя файла для Excel"""
    filenames = {
        'analytics_user_performance': 'analytics_user_performance.xlsx',
        'analytics_user_performance_extended': 'analytics_user_performance_extended.xlsx',
        'analytics_test_statistics': 'analytics_test_statistics.xlsx',
        'analytics_group_performance': 'analytics_group_performance.xlsx',
        'analytics_question_analysis': 'analytics_question_analysis.xlsx',
        # Здесь можно добавить имена файлов для других представлений
    }
    
    return filenames.get(view_name, f'{view_name}.xlsx')


async def get_all_analytics_views(db: AsyncSession):
    result = await db.execute(select(AnalyticsView).order_by(AnalyticsView.sort_order, AnalyticsView.id))
    return result.scalars().all()


async def get_analytics_user_test_question_performance(db: AsyncSession) -> List[Dict[str, Any]]:
    """Получение данных из вью analytics_user_test_question_performance для pivot-отчёта по пользователям и тестам"""
    try:
        stmt = text("SELECT * FROM analytics_user_test_question_performance ORDER BY user_full_name, test_title")
        result = await db.execute(stmt)
        rows = result.fetchall()
        columns = result.keys()
        analytics_data = []
        for row in rows:
            row_dict = {col: row[i] for i, col in enumerate(columns)}
            analytics_data.append(row_dict)
        return analytics_data
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при получении данных из вью analytics_user_test_question_performance: {str(e)}") 


async def get_user_tests_chart_config(db: AsyncSession, user_id: int, limit: int = 10) -> Dict[str, Any]:
    """Формирует JSON-конфиг ApexCharts: топ-N тестов пользователя по последнему результату."""
    try:
        # Берём последний результат по каждому тесту пользователя
        stmt = text(
            """
            WITH ranked AS (
                SELECT r.test_id,
                       t.title AS test_title,
                       r.score,
                       r.completed_at,
                       ROW_NUMBER() OVER (PARTITION BY r.test_id ORDER BY r.completed_at DESC) AS rn
                FROM result r
                JOIN test t ON t.id = r.test_id
                WHERE r.user_id = :user_id AND r.score IS NOT NULL
            )
            SELECT test_title, score
            FROM ranked
            WHERE rn = 1
            ORDER BY score ASC
            LIMIT :limit
            """
        ).bindparams(user_id=user_id, limit=limit)

        res = await db.execute(stmt)
        rows = res.fetchall()
        categories = [row[0] for row in rows]
        data = [row[1] for row in rows]

        colors = ["#33b2df", "#546E7A", "#d4526e", "#13d8aa", "#A5978B", "#2b908f", "#f9a3a4", "#90ee7e", "#f48024", "#69d2e7"]

        return {
            "data": data,
            "colors": colors,
            "categories": categories
        }
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при формировании чарта: {str(e)}") 


async def get_user_tests_pie_config(db: AsyncSession, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """Формирует данные для pie-чарта: агрегирует последние результаты пользователя по тестам в 3 категории.
    Категории:
    - Зеленый: pass == true ("Хорошо сдал тест")
    - Красный: диапазон последней строки шкалы (самый низкий) ("Плохо сдал тест")
    - Желтый: все прочие диапазоны ("Нормально сдал тест")
    Основано на grade_options.scale типа percent и поле result->>'percentage'.
    """
    try:
        stmt = text(
            """
            WITH ranked AS (
                SELECT r.test_id,
                       t.title AS test_title,
                       r.result->>'percentage' AS percentage_text,
                       t.grade_options AS grade_options,
                       r.completed_at,
                       ROW_NUMBER() OVER (PARTITION BY r.test_id ORDER BY r.completed_at DESC) AS rn
                FROM result r
                JOIN test t ON t.id = r.test_id
                WHERE r.user_id = :user_id
            )
            SELECT test_title, percentage_text, grade_options
            FROM ranked
            WHERE rn = 1
            """
        ).bindparams(user_id=user_id)

        res = await db.execute(stmt)
        rows = res.fetchall()

        good_count = 0
        bad_count = 0
        normal_count = 0

        for row in rows:
            percentage_text = row[1]
            try:
                percentage = float(percentage_text) if percentage_text is not None else None
            except (TypeError, ValueError):
                percentage = None

            grade_options = row[2] or {}
            scale = grade_options.get("scale") if isinstance(grade_options, dict) else None
            scale_type = grade_options.get("scaleType") if isinstance(grade_options, dict) else None

            if not scale or scale_type != "percent" or percentage is None:
                # Не хватает данных для классификации — считаем как "Нормально"
                normal_count += 1
                continue

            # Определяем попадание процента в диапазон шкалы
            matched_index = None
            pass_flag = False
            for idx, band in enumerate(scale):
                try:
                    band_min = float(band.get("min"))
                    band_max = float(band.get("max"))
                except (TypeError, ValueError):
                    continue
                if band_min <= percentage <= band_max:
                    matched_index = idx
                    pass_flag = bool(band.get("pass"))
                    break

            if matched_index is None:
                normal_count += 1
                continue

            # pass == true -> зеленый (good)
            if pass_flag:
                good_count += 1
                continue

            # Последняя строка шкалы -> красный (bad)
            if matched_index == len(scale) - 1:
                bad_count += 1
            else:
                normal_count += 1

        data = [
            {"name": "Хорошо сдал тест", "value": good_count, "color": "#00C853"},
            {"name": "Почти сдал тест", "value": normal_count, "color": "#FF9800"},
            {"name": "Плохо сдал тест", "value": bad_count, "color": "#F44336"},
        ]

        total = good_count + normal_count + bad_count
        if total > 0:
            for item in data:
                item["value"] = round(item["value"] * 100.0 / total, 1)
        else:
            for item in data:
                item["value"] = 0.0

        return data
    except SQLAlchemyError as e:
        raise DatabaseException(f"Ошибка при формировании pie-чарта: {str(e)}") 