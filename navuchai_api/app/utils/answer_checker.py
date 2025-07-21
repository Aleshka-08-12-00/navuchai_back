from typing import Dict, Any, Tuple
from app.models import Question
from app.exceptions import BadRequestException
import re

# Проверки одного ответа

def clean_html(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text)

def check_answer(question: Question, answer: Dict[str, Any]) -> Tuple[int, bool, Dict[str, Any]]:
    question_type = question.type.code if question.type else None
    answers = question.answers
    correct_score = 1
    incorrect_score = 0
    if isinstance(answers, dict) and 'settings' in answers:
        settings = answers.get('settings', {})
        correct_score = settings.get('correctScore', 1)
        incorrect_score = settings.get('incorrectScore', 0)
    if question_type == "SINGLE_CHOICE":
        return check_single_choice(question, answer, correct_score, incorrect_score)
    elif question_type == "MULTIPLE_CHOICE":
        return check_multiple_choice(question, answer, correct_score, incorrect_score)
    elif question_type == "TRUE_FALSE":
        return check_true_false(question, answer, correct_score, incorrect_score)
    elif question_type in ["SHORT_ANSWER", "SURVEY", "DESCRIPTIVE"]:
        return correct_score, True, {
            "user_answer": answer.get("value", ""),
            "message": "Ответ принят без проверки"
        }
    elif question_type in ["ESSAY", "FILE", "VOICE"]:
        if "is_correct" in answer:
            is_correct = answer["is_correct"]
            score = correct_score if is_correct else incorrect_score
            details = answer.get("check_details", {})
            details["user_answer"] = answer.get("value", "")
            details["message"] = details.get("message", "Вопрос проверен")
            if "manual_check_required" in details:
                del details["manual_check_required"]
            return score, is_correct, details
        return 0, False, {
            "user_answer": answer.get("value", ""),
            "manual_check_required": True,
            "message": "Требуется ручная проверка ответа"
        }
    else:
        raise BadRequestException(f"Неизвестный тип вопроса: {question_type}")

def check_single_choice(question: Question, answer: Dict[str, Any], correct_score: int, incorrect_score: int) -> Tuple[int, bool, Dict[str, Any]]:
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
    correct_answers = question.answers.get("correctAnswer", [])
    user_answers = answer.get("value", [])
    if not isinstance(correct_answers, list) or not isinstance(user_answers, list):
        return incorrect_score, False, {"error": "Некорректный формат ответов"}
    correct_answers = [clean_html(str(ans)).strip().lower() for ans in correct_answers]
    user_answers = [clean_html(str(ans)).strip().lower() for ans in user_answers]
    is_correct = set(user_answers) == set(correct_answers)
    return correct_score if is_correct else incorrect_score, is_correct, {
        "correct_answers": correct_answers,
        "user_answers": user_answers
    }

def check_true_false(question: Question, answer: Dict[str, Any], correct_score: int, incorrect_score: int) -> Tuple[int, bool, Dict[str, Any]]:
    correct_answer = question.answers.get("correctAnswer", [None])[0]
    user_answer = answer.get("value")
    if correct_answer is None or user_answer is None:
        return incorrect_score, False, {"error": "Отсутствует правильный ответ или ответ пользователя"}
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

# Импортируйте process_test_results из app.test_result.test_result_calculator
from app.test_result.test_result_calculator import process_test_results
