from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.base import Base


class UserGroup(Base):
    __tablename__ = "user_group"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    creator_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    creator = relationship("User", back_populates="created_groups")
    members = relationship("UserGroupMember", back_populates="group", cascade="all, delete-orphan")
    test_accesses = relationship("TestAccess", back_populates="group", cascade="all, delete-orphan") 