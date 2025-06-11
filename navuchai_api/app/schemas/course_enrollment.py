from datetime import datetime
from pydantic import BaseModel

class CourseEnrollmentBase(BaseModel):
    id: int
    course_id: int
    user_id: int
    enrolled_at: datetime
    class Config:
        from_attributes = True
