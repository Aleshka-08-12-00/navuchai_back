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

    created_tests = relationship("Test", back_populates="creator")
    results = relationship("Result", back_populates="user", cascade="all, delete-orphan")
    user_answers = relationship("UserAnswer", back_populates="user", cascade="all, delete-orphan")
    role = relationship("Role", back_populates="users", lazy="joined")
