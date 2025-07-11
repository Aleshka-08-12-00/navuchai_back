from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.role import RoleBase
from app.models.role_enum import RoleCode
from pydantic import ConfigDict


class UserBase(BaseModel):
    name: str
    role_id: int
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    username: str
    email: str
    role: RoleBase
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    role_code: RoleCode


class PasswordChange(BaseModel):
    old_password: str
    new_password: str

    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetResponse(BaseModel):
    message: str
    success: bool
