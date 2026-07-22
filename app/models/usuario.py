from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    analyst = "analyst"
    operator = "operator"
    viewer = "viewer"


class AdminUser(SQLModel, table=True):
    __tablename__ = "admin_users"

    user_id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, unique=True, index=True)
    role: UserRole = Field(default=UserRole.viewer)
    active: bool = Field(default=True)
