from sqlalchemy import Integer, String, Column, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Test(Base):
    __tablename__ = 'test'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    creator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    time_limit = Column(Integer)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    category = relationship("Category", back_populates="tests", single_parent=True)  # Ensure single parent for category
    creator = relationship("User", back_populates="created_tests")
    test_questions = relationship("TestQuestion", back_populates="test")
    results = relationship("Result", back_populates="test")
