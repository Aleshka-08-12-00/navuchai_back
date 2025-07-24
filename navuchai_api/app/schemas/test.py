from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel
from app.schemas.file import FileInDB
from app.models.test import TestAccessEnum, AnswerViewModeEnum
from app.schemas.test_group import TestGroup


class TestBase(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: Optional[int] = None
    access_timestamp: datetime
    status_id: int
    frozen: bool
    locale_id: int
    time_limit: Optional[int] = None
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    percent: Optional[int] = None
    completed: Optional[int] = None
    welcome_message: Optional[str] = None
    goodbye_message: Optional[str] = None
    access: TestAccessEnum
    answer_view_mode: AnswerViewModeEnum
    code: Optional[str] = None
    grade_options: Optional[Dict[str, Any]] = {
        "scale": [
            {"max": 100, "min": 80, "pass": True, "color": "#43a047", "grade": 5},
            {"max": 79, "min": 50, "pass": False, "color": "#ffd54f", "grade": 3},
            {"max": 49, "min": 0, "pass": False, "color": "#b71c1c", "grade": 2}
        ],
        "autoGrade": True,
        "scaleType": "percent",
        "showToUser": True,
        "systemName": "final_grade",
        "displayName": "Итоговая оценка",
        "customMessage": "Ваша оценка: ",
        "hiddenResultMessage": "Спасибо за участие, результаты будут отправлены позже..."
    }

    class Config:
        from_attributes = True


class TestWithDetails(TestBase):
    category_name: str
    creator_name: str
    locale_code: str
    status_name: str
    status_name_ru: Optional[str] = None
    status_color: Optional[str] = None
    image: Optional[FileInDB] = None
    thumbnail: Optional[FileInDB] = None
    code: Optional[str] = None
    group: Optional[TestGroup] = None


class TestWithAccessDetails(TestWithDetails):
    access_status_name: Optional[str] = None
    access_status_code: Optional[str] = None
    access_status_color: Optional[str] = None
    user_percent: Optional[float] = None
    user_completed: Optional[int] = None
    access_code: Optional[str] = None
    done: Optional[bool] = None


class TestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: Optional[int] = None
    access_timestamp: datetime
    status_id: int
    frozen: bool
    locale_id: int
    time_limit: Optional[int] = None
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    welcome_message: Optional[str] = None
    goodbye_message: Optional[str] = None
    access: TestAccessEnum = TestAccessEnum.PRIVATE
    answer_view_mode: AnswerViewModeEnum = AnswerViewModeEnum.USER_ONLY
    grade_options: Optional[Dict[str, Any]] = {
        "scale": [
            {"max": 100, "min": 80, "pass": True, "color": "#43a047", "grade": 5},
            {"max": 79, "min": 50, "pass": False, "color": "#ffd54f", "grade": 3},
            {"max": 49, "min": 0, "pass": False, "color": "#b71c1c", "grade": 2}
        ],
        "autoGrade": True,
        "scaleType": "percent",
        "showToUser": True,
        "systemName": "final_grade",
        "displayName": "Итоговая оценка",
        "customMessage": "Ваша оценка: ",
        "hiddenResultMessage": "Спасибо за участие, результаты будут отправлены позже..."
    }

    class Config:
        from_attributes = True


class TestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    access_timestamp: Optional[datetime] = None
    status_id: Optional[int] = None
    frozen: Optional[bool] = None
    locale_id: Optional[int] = None
    time_limit: Optional[int] = None
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    welcome_message: Optional[str] = None
    goodbye_message: Optional[str] = None
    answer_view_mode: Optional[AnswerViewModeEnum] = None
    grade_options: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class TestResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: Optional[int] = None
    access_timestamp: datetime
    status_id: int
    frozen: bool
    locale_id: int
    time_limit: Optional[int] = None
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    percent: Optional[int] = None
    completed: Optional[int] = None
    welcome_message: Optional[str] = None
    goodbye_message: Optional[str] = None
    access: TestAccessEnum
    answer_view_mode: AnswerViewModeEnum
    created_at: datetime
    updated_at: datetime
    code: Optional[str] = None
    grade_options: Optional[Dict[str, Any]] = {
        "scale": [
            {"max": 100, "min": 80, "pass": True, "color": "#43a047", "grade": 5},
            {"max": 79, "min": 50, "pass": False, "color": "#ffd54f", "grade": 3},
            {"max": 49, "min": 0, "pass": False, "color": "#b71c1c", "grade": 2}
        ],
        "autoGrade": True,
        "scaleType": "percent",
        "showToUser": True,
        "systemName": "final_grade",
        "displayName": "Итоговая оценка",
        "customMessage": "Ваша оценка: ",
        "hiddenResultMessage": "Спасибо за участие, результаты будут отправлены позже..."
    }

    class Config:
        from_attributes = True


class TestListResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category_id: int
    creator_id: Optional[int] = None
    access_timestamp: datetime
    status_id: int
    status_name: str
    status_name_ru: Optional[str] = None
    status_color: Optional[str] = None
    frozen: bool
    locale_id: int
    locale_code: str
    time_limit: Optional[int] = None
    img_id: Optional[int] = None
    thumbnail_id: Optional[int] = None
    image: Optional[FileInDB] = None
    thumbnail: Optional[FileInDB] = None
    percent: Optional[int] = None
    completed: Optional[int] = None
    access: TestAccessEnum
    answer_view_mode: AnswerViewModeEnum
    grade_options: Optional[Dict[str, Any]] = {
        "scale": [
            {"max": 100, "min": 80, "pass": True, "color": "#43a047", "grade": 5},
            {"max": 79, "min": 50, "pass": False, "color": "#ffd54f", "grade": 3},
            {"max": 49, "min": 0, "pass": False, "color": "#b71c1c", "grade": 2}
        ],
        "autoGrade": True,
        "scaleType": "percent",
        "showToUser": True,
        "systemName": "final_grade",
        "displayName": "Итоговая оценка",
        "customMessage": "Ваша оценка: ",
        "hiddenResultMessage": "Спасибо за участие, результаты будут отправлены позже..."
    }

    class Config:
        from_attributes = True
