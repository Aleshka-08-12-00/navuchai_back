from datetime import datetime

from pydantic import BaseModel


class CourseRatingBase(BaseModel):
    id: int
    course_id: int
    user_id: int
    rating: int
    created_at: datetime

    class Config:
        from_attributes = True


class CourseRatingCreate(BaseModel):
    rating: int
