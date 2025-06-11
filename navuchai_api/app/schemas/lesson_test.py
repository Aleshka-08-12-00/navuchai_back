from pydantic import BaseModel

class LessonTestBase(BaseModel):
    id: int
    lesson_id: int
    test_id: int
    required: bool
    class Config:
        from_attributes = True
class LessonTestCreate(BaseModel):

    lesson_id: int
    test_id: int
    required: bool = True
