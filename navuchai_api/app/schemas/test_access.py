from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TestAccessBase(BaseModel):
    test_id: int
    user_id: Optional[int] = None
    group_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status_id: int
    access_code: Optional[str] = None
    is_completed: Optional[bool] = False


class TestAccessCreate(BaseModel):
    test_id: int
    user_id: int
    status_id: int = 1

    class Config:
        from_attributes = True


class TestAccessGroupCreate(BaseModel):
    test_id: int
    group_id: int
    status_id: Optional[int] = None

    class Config:
        from_attributes = True


class TestAccessResponse(BaseModel):
    id: int
    test_id: int
    user_id: int
    group_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status_id: int
    access_code: Optional[str] = None
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    role_id: Optional[int] = None
    role: Optional[dict] = None

    class Config:
        from_attributes = True


class GuestTestAccessCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    test_id: int

    class Config:
        from_attributes = True


class GuestTestAccessResponse(BaseModel):
    access_code: Optional[str] = None
    user_id: Optional[int] = None
    message: str

    class Config:
        from_attributes = True


class GuestUserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    access_id: int
    access_code: Optional[str] = None
    status_id: int
    status_name: Optional[str] = None
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 