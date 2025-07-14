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
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role_id: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    img_id: Optional[int] = None
    organization_id: Optional[int] = None
    position_id: Optional[int] = None
    department_id: Optional[int] = None
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True


class OrganizationResponse(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class PositionResponse(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class DepartmentResponse(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    username: str
    email: str
    role: RoleBase
    created_at: datetime
    updated_at: datetime
    photo_url: Optional[str] = None
    organization: Optional[OrganizationResponse] = None
    position: Optional[PositionResponse] = None
    department: Optional[DepartmentResponse] = None
    phone_number: Optional[str] = None
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

class OrganizationBase(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class PositionBase(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class DepartmentBase(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class OrganizationList(BaseModel):
    organizations: list[OrganizationBase]

class PositionList(BaseModel):
    positions: list[PositionBase]

class DepartmentList(BaseModel):
    departments: list[DepartmentBase]
