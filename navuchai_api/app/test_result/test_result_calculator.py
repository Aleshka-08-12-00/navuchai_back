from typing import Dict, Any, List
from app.schemas.result import UserAnswerCreate
from app.exceptions import BadRequestException
from app.utils.answer_checker import check_answer

def calculate_grade_by_percentage(percentage: float, grade_options: Dict[str, Any]) -> str:
    scale = grade_options.get("scale", [])
    sorted_scale = sorted(scale, key=lambda x: x.get("min", 0), reverse=True)
    for grade_range in sorted_scale:
        min_val = grade_range.get("min", 0)
        max_val = grade_range.get("max", 100)
        grade = grade_range.get("grade", "2")
        if min_val <= percentage <= max_val:
            return str(grade)
    return str(scale[-1].get("grade", "2")) if scale else "2"

def calculate_grade_by_points(points: int, grade_options: Dict[str, Any]) -> str:
    scale = grade_options.get("scale", [])
    sorted_scale = sorted(scale, key=lambda x: x.get("min", 0), reverse=True)
    for grade_range in sorted_scale:
        min_val = grade_range.get("min", 0)
        max_val = grade_range.get("max", 100)
        grade = grade_range.get("grade", "2")
        if min_val <= points <= max_val:
            return str(grade)
    return str(scale[-1].get("grade", "2")) if scale else "2"

def get_pass_status_from_scale(value, grade_options):
    scale = (grade_options or {}).get("scale", [])
    sorted_scale = sorted(scale, key=lambda x: x.get("min", 0), reverse=True)
    for grade_range in sorted_scale:
        min_val = grade_range.get("min", 0)
        max_val = grade_range.get("max", 100)
        if min_val <= value <= max_val:
            return grade_range.get("pass", False)
    return False

def process_test_results(questions: List[Dict[str, Any]], answers: List[UserAnswerCreate], test_time_limit: int = 0, grade_options: Dict[str, Any] = None) -> Dict[str, Any]:
    if not questions:
        raise BadRequestException("Список вопросов пуст")
    if not answers:
        raise BadRequestException("Список ответов пуст")
    total_score = 0
    max_possible_score = 0
    checked_answers = []
    answers_dict = {answer.question_id: answer for answer in answers}
    time_start = min(answer.time_start for answer in answers) if answers else None
    time_end = max(answer.time_end for answer in answers) if answers else None
    total_time_seconds = int((time_end - time_start).total_seconds()) if time_start and time_end else 0
    if test_time_limit > 0 and total_time_seconds > test_time_limit:
        raise BadRequestException(f"Превышен лимит времени на тест ({test_time_limit} секунд)")
    for question_data in questions:
        question = question_data['question']
        max_possible_score += question_data['max_score']
        answer = answers_dict.get(question.id)
        if answer:
            question_time_seconds = int((answer.time_end - answer.time_start).total_seconds())
            question_time_limit = question.time_limit or 0
            is_time_exceeded = question_time_limit > 0 and question_time_seconds > question_time_limit
            if is_time_exceeded:
                score = 0
                is_correct = False
                check_details = {"message": f"Превышен лимит времени на вопрос ({question_time_limit} секунд)"}
            else:
                score, is_correct, check_details = check_answer(question, answer.answer)
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
    manual_check_required = any(
        ans.get("check_details", {}).get("manual_check_required") is True
        for ans in checked_answers
    )
    result = {
        "checked_answers": checked_answers,
        "time_start": time_start,
        "time_end": time_end,
        "total_time_seconds": total_time_seconds,
        "test_time_limit": test_time_limit
    }
    grade = None
    color = None
    if manual_check_required:
        result["manual_check_required"] = True
        result["message"] = "Тест содержит вопросы, требующие ручной проверки. Итоговый результат будет доступен после проверки."
    else:
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
        def get_pass_status_from_scale(value, grade_options):
            scale = (grade_options or {}).get("scale", [])
            sorted_scale = sorted(scale, key=lambda x: x.get("min", 0), reverse=True)
            for grade_range in sorted_scale:
                min_val = grade_range.get("min", 0)
                max_val = grade_range.get("max", 100)
                if min_val <= value <= max_val:
                    return grade_range.get("pass", False)
            return False
        if grade_options:
            if grade_options.get("scaleType") == "percent":
                is_passed = get_pass_status_from_scale(percentage, grade_options)
            elif grade_options.get("scaleType") == "points":
                is_passed = get_pass_status_from_scale(total_score, grade_options)
            else:
                is_passed = percentage >= 60
        else:
            is_passed = percentage >= 60
        result["message"] = "Вы прошли тест" if is_passed else "Недостаточно баллов для прохождения теста"
        result["is_passed"] = is_passed
        if grade is not None:
            result["grade"] = grade
        if color is not None:
            result["color"] = color
    result["total_score"] = total_score
    result["max_possible_score"] = max_possible_score
    result["percentage"] = percentage
    return result 