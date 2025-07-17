from typing import Dict, Any, List, Tuple
from app.models import Question, TestQuestion
from app.schemas.result import UserAnswerCreate
from app.exceptions import BadRequestException
import re


def clean_html(text: str) -> str:
    """Удаляет HTML-теги из текста"""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text)


def process_test_results(questions: List[Dict[str, Any]], answers: List[UserAnswerCreate], test_time_limit: int = 0, grade_options: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Обрабатывает результаты теста и возвращает словарь с результатами

    Args:
        questions: Список вопросов с их параметрами
        answers: Список ответов пользователя
        test_time_limit: Лимит времени на весь тест в секундах (0 - без лимита)

    Returns:
        Dict[str, Any]: Словарь с результатами теста

    Raises:
        BadRequestException: При некорректных данных или превышении лимита времени
    """
    if not questions:
        raise BadRequestException("Список вопросов пуст")
    if not answers:
        raise BadRequestException("Список ответов пуст")

    total_score = 0
    max_possible_score = 0
    checked_answers = []

    # Создаем словарь ответов для быстрого поиска
    answers_dict = {answer.question_id: answer for answer in answers}

    # Находим общее время начала и окончания теста
    time_start = min(answer.time_start for answer in answers) if answers else None
    time_end = max(answer.time_end for answer in answers) if answers else None
    total_time_seconds = int((time_end - time_start).total_seconds()) if time_start and time_end else 0

    # Проверяем лимит времени на весь тест
    if test_time_limit > 0 and total_time_seconds > test_time_limit:
        raise BadRequestException(f"Превышен лимит времени на тест ({test_time_limit} секунд)")

    for question_data in questions:
        question = question_data['question']
        max_possible_score += question_data['max_score']
        answer = answers_dict.get(question.id)

        if answer:
            # Рассчитываем время на вопрос
            question_time_seconds = int((answer.time_end - answer.time_start).total_seconds())

            # Проверяем лимит времени на вопрос
            question_time_limit = question.time_limit or 0
            is_time_exceeded = question_time_limit > 0 and question_time_seconds > question_time_limit

            # Если превышен лимит времени, не засчитываем ответ
            if is_time_exceeded:
                score = 0
                is_correct = False
                check_details = {"message": f"Превышен лимит времени на вопрос ({question_time_limit} секунд)"}
            else:
                score, is_correct, check_details = check_answer(question, answer.answer)

            # Получаем тип вопроса в виде строки
            question_type = question.type.code if question.type else "UNKNOWN"

            checked_answers.append({
                "question_id": question.id,
                "question_text": question.text,
                "question_type": question_type,
                "max_score": question_data['max_score'],
                "score": score,
                "is_correct": is_correct,
                "check_details": check_details,
                "options": question.answers,
                "time_start": answer.time_start,
                "time_end": answer.time_end,
                "time_seconds": question_time_seconds,
                "time_limit": question_time_limit,
                "is_time_exceeded": is_time_exceeded
            })
            total_score += score

    percentage = round((total_score / max_possible_score * 100), 1) if max_possible_score > 0 else 0

    def get_pass_status_from_scale(value, grade_options):
        scale = (grade_options or {}).get("scale", [])
        scale_type = (grade_options or {}).get("scaleType", "percent")
        sorted_scale = sorted(scale, key=lambda x: x.get("min", 0), reverse=True)
        for grade_range in sorted_scale:
            min_val = grade_range.get("min", 0)
            max_val = grade_range.get("max", 100)
            if min_val <= value <= max_val:
                return grade_range.get("pass", False)
        return False

    is_passed = False
    if grade_options:
        if grade_options.get("scaleType") == "percent":
            is_passed = get_pass_status_from_scale(percentage, grade_options)
        elif grade_options.get("scaleType") == "points":
            is_passed = get_pass_status_from_scale(total_score, grade_options)
        else:
            is_passed = False
    else:
        is_passed = percentage >= 60

    result = {
        "total_score": total_score,
        "max_possible_score": max_possible_score,
        "percentage": percentage,
        "checked_answers": checked_answers,
        "time_start": time_start,
        "time_end": time_end,
        "total_time_seconds": total_time_seconds,
        "test_time_limit": test_time_limit,
        "is_passed": is_passed,
        "message": None
    }

    # Добавляем оценку на основе настроек теста
    grade = None
    color = None
    if grade_options and grade_options.get("scaleType") == "percent":
        scale = grade_options.get("scale", [])
        sorted_scale = sorted(scale, key=lambda x: x.get("min", 0), reverse=True)
        grade_range = None
        for gr in sorted_scale:
            if gr.get("min", 0) <= percentage <= gr.get("max", 100):
                grade_range = gr
                break
        if grade_range:
            grade = str(grade_range.get("grade", "2"))
            color = grade_range.get("color")
        else:
            grade = str(scale[-1].get("grade", "2")) if scale else "2"
            color = scale[-1].get("color") if scale else None
        result["grade"] = grade
        result["color"] = color
    elif grade_options and grade_options.get("scaleType") == "points":
        scale = grade_options.get("scale", [])
        sorted_scale = sorted(scale, key=lambda x: x.get("min", 0), reverse=True)
        grade_range = None
        for gr in sorted_scale:
            if gr.get("min", 0) <= total_score <= gr.get("max", 100):
                grade_range = gr
                break
        if grade_range:
            grade = str(grade_range.get("grade", "2"))
            color = grade_range.get("color")
        else:
            grade = str(scale[-1].get("grade", "2")) if scale else "2"
            color = scale[-1].get("color") if scale else None
        result["grade"] = grade
        result["color"] = color

    # Добавляем customMessage и hiddenResultMessage из grade_options
    if grade_options:
        custom_message = grade_options.get("customMessage")
        hidden_result_message = grade_options.get("hiddenResultMessage")
        if custom_message:
            result["customMessage"] = custom_message
        if hidden_result_message:
            result["hiddenResultMessage"] = hidden_result_message
        # Добавляем autoGrade и showToUser
        if "autoGrade" in grade_options:
            result["autoGrade"] = grade_options["autoGrade"]
        if "showToUser" in grade_options:
            result["showToUser"] = grade_options["showToUser"]
        if "scaleType" in grade_options:
            result["scaleType"] = grade_options["scaleType"]
        if "displayName" in grade_options:
            result["displayName"] = grade_options["displayName"]

    # Формируем message в зависимости от результата
    if is_passed:
        result["message"] = "Вы прошли тест"
    else:
        # Проверка превышения лимита времени на тест
        if test_time_limit > 0 and total_time_seconds > test_time_limit:
            result["message"] = "Время на выполнение теста истекло"
        else:
            result["message"] = "Недостаточно баллов для прохождения теста"

    return result


def check_answer(question: Question, answer: Dict[str, Any]) -> Tuple[int, bool, Dict[str, Any]]:
    """
    Проверяет ответ на вопрос и возвращает кортеж (score, is_correct, check_details)

    Args:
        question: Объект вопроса
        answer: Ответ пользователя

    Returns:
        Tuple[int, bool, Dict[str, Any]]: (балл, правильность ответа, детали проверки)

    Raises:
        BadRequestException: При неизвестном типе вопроса
    """
    question_type = question.type.code if question.type else None
    
    # Получаем настройки баллов из вопроса
    answers = question.answers
    correct_score = 1  # значение по умолчанию
    incorrect_score = 0  # значение по умолчанию
    if isinstance(answers, dict) and 'settings' in answers:
        settings = answers.get('settings', {})
        correct_score = settings.get('correctScore', 1)
        incorrect_score = settings.get('incorrectScore', 0)
    
    if question_type == "SINGLE_CHOICE":
        return check_single_choice(question, answer, correct_score, incorrect_score)
    elif question_type == "MULTIPLE_CHOICE":
        return check_multiple_choice(question, answer, correct_score, incorrect_score)
    elif question_type == "TEXT":
        return check_text(question, answer, correct_score, incorrect_score)
    elif question_type == "NUMBER":
        return check_number(question, answer, correct_score, incorrect_score)
    elif question_type == "TRUE_FALSE":
        return check_true_false(question, answer, correct_score, incorrect_score)
    elif question_type in ["SHORT_ANSWER", "SURVEY", "DESCRIPTIVE"]:
        # Для этих типов вопросов не проверяем правильность ответа
        return correct_score, True, {
            "user_answer": answer.get("value", ""),
            "message": "Ответ принят без проверки"
        }
    else:
        raise BadRequestException(f"Неизвестный тип вопроса: {question_type}")


def check_single_choice(question: Question, answer: Dict[str, Any], correct_score: int, incorrect_score: int) -> Tuple[int, bool, Dict[str, Any]]:
    """Проверяет ответ на вопрос с одним вариантом ответа"""
    correct_answer = question.answers.get("correctAnswer", [None])[0]
    user_answer = answer.get("value")
    
    if correct_answer is None or user_answer is None:
        return incorrect_score, False, {"error": "Отсутствует правильный ответ или ответ пользователя"}
    
    is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()
    return correct_score if is_correct else incorrect_score, is_correct, {
        "correct_answer": correct_answer,
        "user_answer": user_answer
    }


def check_multiple_choice(question: Question, answer: Dict[str, Any], correct_score: int, incorrect_score: int) -> Tuple[int, bool, Dict[str, Any]]:
    """Проверяет ответ на вопрос с несколькими вариантами ответа"""
    correct_answers = question.answers.get("correctAnswer", [])
    user_answers = answer.get("value", [])
    
    if not isinstance(correct_answers, list) or not isinstance(user_answers, list):
        return incorrect_score, False, {"error": "Некорректный формат ответов"}
    
    # Очищаем HTML-теги и приводим к нижнему регистру для сравнения
    correct_answers = [clean_html(str(ans)).strip().lower() for ans in correct_answers]
    user_answers = [clean_html(str(ans)).strip().lower() for ans in user_answers]
    
    # Проверяем, что все ответы пользователя правильные и нет лишних
    is_correct = set(user_answers) == set(correct_answers)
    return correct_score if is_correct else incorrect_score, is_correct, {
        "correct_answers": correct_answers,
        "user_answers": user_answers
    }


def check_text(question: Question, answer: Dict[str, Any], correct_score: int, incorrect_score: int) -> Tuple[int, bool, Dict[str, Any]]:
    """Проверяет текстовый ответ"""
    correct_answer = question.answers.get("correctAnswer", [""])[0]
    user_answer = answer.get("value", "").strip().lower()
    
    if not correct_answer:
        return incorrect_score, False, {"error": "Отсутствует правильный ответ"}
    
    is_correct = user_answer == correct_answer.strip().lower()
    return correct_score if is_correct else incorrect_score, is_correct, {
        "correct_answer": correct_answer,
        "user_answer": user_answer
    }


def check_number(question: Question, answer: Dict[str, Any], correct_score: int, incorrect_score: int) -> Tuple[int, bool, Dict[str, Any]]:
    """Проверяет числовой ответ"""
    try:
        correct_answer = float(question.answers.get("correctAnswer", [0])[0])
        user_answer = float(answer.get("value", 0))
        
        is_correct = abs(user_answer - correct_answer) < 0.0001  # Учитываем погрешность для чисел с плавающей точкой
        return correct_score if is_correct else incorrect_score, is_correct, {
            "correct_answer": correct_answer,
            "user_answer": user_answer
        }
    except (ValueError, TypeError):
        return incorrect_score, False, {"error": "Некорректный формат числового ответа"}


def check_true_false(question: Question, answer: Dict[str, Any], correct_score: int, incorrect_score: int) -> Tuple[int, bool, Dict[str, Any]]:
    """Проверяет ответ на вопрос типа TRUE/FALSE"""
    correct_answer = question.answers.get("correctAnswer", [None])[0]
    user_answer = answer.get("value")
    
    if correct_answer is None or user_answer is None:
        return incorrect_score, False, {"error": "Отсутствует правильный ответ или ответ пользователя"}
    
    # Преобразуем ответы в булевы значения
    try:
        user_bool = str(user_answer).strip().lower() in ['true', '1', 'yes', 'да', 'верно', 'да']
        correct_bool = str(correct_answer).strip().lower() in ['true', '1', 'yes', 'да', 'верно', 'да']
        
        is_correct = user_bool == correct_bool
        return correct_score if is_correct else incorrect_score, is_correct, {
            "correct_answer": correct_answer,
            "user_answer": user_answer
        }
    except Exception as e:
        return incorrect_score, False, {"error": f"Ошибка при проверке ответа TRUE/FALSE: {str(e)}"}


def calculate_grade_by_percentage(percentage: float, grade_options: Dict[str, Any]) -> str:
    """
    Рассчитывает оценку на основе процента правильных ответов
    
    Args:
        percentage: Процент правильных ответов (0-100)
        grade_options: Настройки оценивания теста
        
    Returns:
        str: Оценка (например, "5", "4", "3", "2")
    """
    scale = grade_options.get("scale", [])
    
    # Сортируем шкалу по убыванию минимального значения
    sorted_scale = sorted(scale, key=lambda x: x.get("min", 0), reverse=True)
    
    # Ищем подходящую оценку
    for grade_range in sorted_scale:
        min_val = grade_range.get("min", 0)
        max_val = grade_range.get("max", 100)
        grade = grade_range.get("grade", "2")
        
        if min_val <= percentage <= max_val:
            return str(grade)
    
    # Если не найдена подходящая оценка, возвращаем минимальную
    return str(scale[-1].get("grade", "2")) if scale else "2"


def calculate_grade_by_points(points: int, grade_options: Dict[str, Any]) -> str:
    """
    Рассчитывает оценку на основе количества баллов
    
    Args:
        points: Количество набранных баллов
        grade_options: Настройки оценивания теста
        
    Returns:
        str: Оценка (например, "5", "4", "3", "2")
    """
    scale = grade_options.get("scale", [])
    
    # Сортируем шкалу по убыванию минимального значения
    sorted_scale = sorted(scale, key=lambda x: x.get("min", 0), reverse=True)
    
    # Ищем подходящую оценку
    for grade_range in sorted_scale:
        min_val = grade_range.get("min", 0)
        max_val = grade_range.get("max", 100)
        grade = grade_range.get("grade", "2")
        
        if min_val <= points <= max_val:
            return str(grade)
    
    # Если не найдена подходящая оценка, возвращаем минимальную
    return str(scale[-1].get("grade", "2")) if scale else "2"
