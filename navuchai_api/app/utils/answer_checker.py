from typing import Dict, Any, List, Tuple
from app.models import Question, TestQuestion
from app.schemas.result import UserAnswerCreate
import re


def clean_html(text: str) -> str:
    """Удаляет HTML-теги из текста"""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text)


def check_answer(question: Question, user_answer: Dict[str, Any], max_score: int) -> Tuple[bool, int, Dict[str, Any]]:
    """
    Проверяет ответ пользователя и возвращает результат проверки
    
    Args:
        question: Объект вопроса
        user_answer: Ответ пользователя
        max_score: Максимальный балл за вопрос
        
    Returns:
        Tuple[bool, int, Dict[str, Any]]: (правильность ответа, полученные баллы, детали проверки)
    """
    question_type = question.type
    question_data = question.answers

    # Получаем настройки вопроса
    settings = question_data.get('settings', {})
    correct_score = settings.get('correctScore', 1)
    incorrect_score = settings.get('incorrectScore', 0)
    correct_answers = question_data.get('correctAnswer', [])

    # Подготовка результата проверки
    check_result = {
        'is_correct': False,
        'user_answer': user_answer,
        'correct_answer': correct_answers,
        'max_score': max_score,
        'score': 0,
        'details': {}
    }

    # Для DESCRIPTIVE и SURVEY пока не делаем проверку
    if question_type in ['DESCRIPTIVE', 'SURVEY']:
        check_result.update({
            'is_correct': True,
            'score': max_score,
            'details': {
                'message': 'Этот тип вопроса не требует автоматической проверки'
            }
        })
        return True, max_score, check_result

    if question_type == 'SINGLE_CHOICE':
        # Проверка для вопроса с одним правильным ответом
        user_choice = user_answer.get('value', '')
        is_correct = user_choice in correct_answers
        score = correct_score if is_correct else incorrect_score

        check_result.update({
            'is_correct': is_correct,
            'score': score,
            'details': {
                'user_choice': user_choice,
                'correct_choice': correct_answers[0] if correct_answers else None,
                'settings': settings
            }
        })

    elif question_type == 'MULTIPLE_CHOICE':
        # Проверка для вопроса с несколькими правильными ответами
        user_choices = user_answer.get('value', [])
        correct_choices = set(correct_answers)

        # Если все правильные ответы выбраны и нет лишних - полный балл
        if set(user_choices) == correct_choices:
            score = correct_score
            is_correct = True
        # Если есть правильные ответы, но не все - частичный балл
        elif set(user_choices).intersection(correct_choices):
            # Вычисляем процент правильных ответов
            correct_count = len(set(user_choices).intersection(correct_choices))
            total_correct = len(correct_choices)
            score = int((correct_count / total_correct) * correct_score)
            is_correct = True
        else:
            score = incorrect_score
            is_correct = False

        check_result.update({
            'is_correct': is_correct,
            'score': score,
            'details': {
                'user_choices': user_choices,
                'correct_choices': list(correct_choices),
                'correct_count': len(set(user_choices).intersection(correct_choices)),
                'total_correct': len(correct_choices),
                'settings': settings
            }
        })

    elif question_type == 'TRUE_FALSE':
        # Проверка для вопроса Да/Нет
        user_choice = user_answer.get('value', '')
        is_correct = user_choice in correct_answers
        score = correct_score if is_correct else incorrect_score

        check_result.update({
            'is_correct': is_correct,
            'score': score,
            'details': {
                'user_choice': user_choice,
                'correct_choice': correct_answers[0] if correct_answers else None,
                'settings': settings
            }
        })

    return is_correct, score, check_result


def process_test_results(questions: List[Dict[str, Any]], user_answers: List[UserAnswerCreate]) -> Dict[str, Any]:
    """
    Обрабатывает все ответы пользователя на тест
    
    Args:
        questions: Список вопросов с их параметрами
        user_answers: Список ответов пользователя
        
    Returns:
        Dict[str, Any]: Результат проверки всего теста
    """
    total_score = 0
    max_possible_score = 0
    checked_answers = []

    # Создаем словарь ответов пользователя для быстрого доступа
    user_answers_dict = {answer.question_id: answer.answer for answer in user_answers}

    for question_data in questions:
        question = question_data['question']
        max_score = question_data['max_score']
        max_possible_score += max_score

        # Получаем ответ пользователя для текущего вопроса
        user_answer = user_answers_dict.get(question.id, {})

        # Проверяем ответ
        is_correct, score, check_result = check_answer(question, user_answer, max_score)
        total_score += score

        checked_answers.append({
            'question_id': question.id,
            'question_text': question.text,
            'question_type': question.type,
            'max_score': max_score,
            'score': score,
            'is_correct': is_correct,
            'check_details': check_result
        })

    # Вычисляем процент правильных ответов
    percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0

    return {
        'total_score': total_score,
        'max_possible_score': max_possible_score,
        'percentage': round(percentage, 2),
        'checked_answers': checked_answers
    }
