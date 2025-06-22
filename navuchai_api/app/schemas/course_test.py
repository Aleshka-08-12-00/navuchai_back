from pydantic import BaseModel


class CourseTestBase(BaseModel):
    id: int
    course_id: int
    test_id: int
    required: bool

    class Config:
        from_attributes = True


class CourseTestCreate(BaseModel):
    course_id: int
    test_id: int
    required: bool = True
