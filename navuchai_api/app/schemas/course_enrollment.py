from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

class CourseEnrollmentBase(BaseModel):
    id: int
    course_id: int
    user_id: int
    enrolled_at: datetime
    class Config:
        from_attributes = True


class FileInfo(BaseModel):
    id: int
    type: Optional[str]
    name: str
    size: int
    path: str
    provider: Optional[str]
    created_at: datetime
    updated_at: datetime
    creator_id: int
    class Config:
        from_attributes = True


class UserCourseInfo(BaseModel):
    course_id: int
    course_title: str
    enrolled_at: datetime


class UserCoursesGrouped(BaseModel):
    user_id: int
    user_name: str
    user_email: str
    user_img: Optional[FileInfo]
    user_thumbnail: Optional[FileInfo]
    courses: List[UserCourseInfo]
