from sqlalchemy import Integer, String, Column, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey('role.id'), nullable=False, default=1)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    img_id = Column(Integer, ForeignKey('file.id', ondelete='SET NULL'), nullable=True)
    thumbnail_id = Column(Integer, ForeignKey('file.id', ondelete='SET NULL'), nullable=False, default=175)
    organization_id = Column(Integer, ForeignKey('organization.id', ondelete='SET NULL'), nullable=True)
    position_id = Column(Integer, ForeignKey('position.id', ondelete='SET NULL'), nullable=True)
    department_id = Column(Integer, ForeignKey('department.id', ondelete='SET NULL'), nullable=True)
    phone_number = Column(String(20), nullable=True)

    img = relationship("File", foreign_keys=[img_id], lazy="joined")
    thumbnail = relationship("File", foreign_keys=[thumbnail_id], lazy="joined")
    organization = relationship("Organization", foreign_keys=[organization_id], lazy="joined")
    position = relationship("Position", foreign_keys=[position_id], lazy="joined")
    department = relationship("Department", foreign_keys=[department_id], lazy="joined")

    created_tests = relationship("Test", back_populates="creator")
    created_groups = relationship("UserGroup", back_populates="creator")
    group_memberships = relationship("UserGroupMember", back_populates="user", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="user", cascade="all, delete-orphan")
    user_answers = relationship("UserAnswer", back_populates="user", cascade="all, delete-orphan")
    role = relationship("Role", back_populates="users", lazy="joined")
    test_accesses = relationship("TestAccess", back_populates="user", cascade="all, delete-orphan")
