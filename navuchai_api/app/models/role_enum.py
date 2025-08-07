from enum import Enum


class RoleCode(str, Enum):
    ROOT = "root"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"
