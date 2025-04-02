from sqlalchemy import Integer, Column, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class TestQuestion(Base):
    __tablename__ = 'test_question'

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('question.id'), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    test = relationship("Test", back_populates="test_questions")
    question = relationship("Question", back_populates="test_questions")
