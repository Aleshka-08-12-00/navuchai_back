from enum import Enum


class RoleCode(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
