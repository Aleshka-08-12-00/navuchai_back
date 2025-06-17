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


def process_test_results(questions: List[Dict[str, Any]], answers: List[UserAnswerCreate], test_time_limit: int = 0) -> Dict[str, Any]:
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
    is_passed = percentage >= 60

    return {
        "total_score": total_score,
        "max_possible_score": max_possible_score,
        "percentage": percentage,
        "checked_answers": checked_answers,
        "time_start": time_start,
        "time_end": time_end,
        "total_time_seconds": total_time_seconds,
        "test_time_limit": test_time_limit,
        "is_passed": is_passed,
        "message": "Тест не пройден: процент выполнения меньше 60%" if not is_passed else None
    }


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
    
    if question_type == "SINGLE_CHOICE":
        return check_single_choice(question, answer)
    elif question_type == "MULTIPLE_CHOICE":
        return check_multiple_choice(question, answer)
    elif question_type == "TEXT":
        return check_text(question, answer)
    elif question_type == "NUMBER":
        return check_number(question, answer)
    elif question_type == "TRUE_FALSE":
        return check_true_false(question, answer)
    elif question_type in ["SHORT_ANSWER", "SURVEY", "DESCRIPTIVE"]:
        # Для этих типов вопросов не проверяем правильность ответа
        return 1, True, {
            "user_answer": answer.get("value", ""),
            "message": "Ответ принят без проверки"
        }
    else:
        raise BadRequestException(f"Неизвестный тип вопроса: {question_type}")


def check_single_choice(question: Question, answer: Dict[str, Any]) -> Tuple[int, bool, Dict[str, Any]]:
    """Проверяет ответ на вопрос с одним вариантом ответа"""
    correct_answer = question.answers.get("correctAnswer", [None])[0]
    user_answer = answer.get("value")
    
    if correct_answer is None or user_answer is None:
        return 0, False, {"error": "Отсутствует правильный ответ или ответ пользователя"}
    
    is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()
    return 1 if is_correct else 0, is_correct, {
        "correct_answer": correct_answer,
        "user_answer": user_answer
    }


def check_multiple_choice(question: Question, answer: Dict[str, Any]) -> Tuple[int, bool, Dict[str, Any]]:
    """Проверяет ответ на вопрос с несколькими вариантами ответа"""
    correct_answers = question.answers.get("correctAnswer", [])
    user_answers = answer.get("value", [])
    
    if not isinstance(correct_answers, list) or not isinstance(user_answers, list):
        return 0, False, {"error": "Некорректный формат ответов"}
    
    # Очищаем HTML-теги и приводим к нижнему регистру для сравнения
    correct_answers = [clean_html(str(ans)).strip().lower() for ans in correct_answers]
    user_answers = [clean_html(str(ans)).strip().lower() for ans in user_answers]
    
    # Проверяем, что все ответы пользователя правильные и нет лишних
    is_correct = set(user_answers) == set(correct_answers)
    return 1 if is_correct else 0, is_correct, {
        "correct_answers": correct_answers,
        "user_answers": user_answers
    }


def check_text(question: Question, answer: Dict[str, Any]) -> Tuple[int, bool, Dict[str, Any]]:
    """Проверяет текстовый ответ"""
    correct_answer = question.answers.get("correctAnswer", [""])[0]
    user_answer = answer.get("value", "").strip().lower()
    
    if not correct_answer:
        return 0, False, {"error": "Отсутствует правильный ответ"}
    
    is_correct = user_answer == correct_answer.strip().lower()
    return 1 if is_correct else 0, is_correct, {
        "correct_answer": correct_answer,
        "user_answer": user_answer
    }


def check_number(question: Question, answer: Dict[str, Any]) -> Tuple[int, bool, Dict[str, Any]]:
    """Проверяет числовой ответ"""
    try:
        correct_answer = float(question.answers.get("correctAnswer", [0])[0])
        user_answer = float(answer.get("value", 0))
        
        is_correct = abs(user_answer - correct_answer) < 0.0001  # Учитываем погрешность для чисел с плавающей точкой
        return 1 if is_correct else 0, is_correct, {
            "correct_answer": correct_answer,
            "user_answer": user_answer
        }
    except (ValueError, TypeError):
        return 0, False, {"error": "Некорректный формат числового ответа"}


def check_true_false(question: Question, answer: Dict[str, Any]) -> Tuple[int, bool, Dict[str, Any]]:
    """Проверяет ответ на вопрос типа TRUE/FALSE"""
    correct_answer = question.answers.get("correctAnswer", [None])[0]
    user_answer = answer.get("value")
    
    if correct_answer is None or user_answer is None:
        return 0, False, {"error": "Отсутствует правильный ответ или ответ пользователя"}
    
    # Преобразуем ответы в булевы значения
    try:
        user_bool = str(user_answer).strip().lower() in ['true', '1', 'yes', 'да', 'верно', 'да']
        correct_bool = str(correct_answer).strip().lower() in ['true', '1', 'yes', 'да', 'верно', 'да']
        
        is_correct = user_bool == correct_bool
        return 1 if is_correct else 0, is_correct, {
            "correct_answer": correct_answer,
            "user_answer": user_answer
        }
    except Exception as e:
        return 0, False, {"error": f"Ошибка при проверке ответа TRUE/FALSE: {str(e)}"}
