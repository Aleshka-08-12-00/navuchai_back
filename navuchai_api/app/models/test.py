from sqlalchemy import Integer, String, Column, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Test(Base):
    __tablename__ = 'test'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    creator_id = Column(Integer, ForeignKey('user.id'))
    time_limit = Column(Integer)
    access_timestamp = Column(TIMESTAMP, nullable=False)
    status = Column(String, nullable=False)
    frozen = Column(Boolean, nullable=False)
    locale = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    category = relationship("Category", back_populates="tests", single_parent=True)
    creator = relationship("User", back_populates="created_tests")
    test_questions = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="test")
