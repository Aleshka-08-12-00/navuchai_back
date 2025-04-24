from pydantic import BaseModel

from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    username: str
    role_id: int


class UserOut(BaseModel):
    id: int
    name: str
    email: Optional[str]
    username: Optional[str]
    role_id: int
    role_code: str
    role_name: str

    class Config:
        orm_mode = True
