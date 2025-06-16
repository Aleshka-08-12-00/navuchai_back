from sqlalchemy import Integer, String, Column, TIMESTAMP, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Question(Base):
    __tablename__ = 'question'

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    text_abstract = Column(String, nullable=False)
    type_id = Column(Integer, ForeignKey('question_type.id'), nullable=False)
    reviewable = Column(Boolean, nullable=False)
    answers = Column(JSONB, nullable=False)
    time_limit = Column(Integer, nullable=True, default=0)  # Лимит времени в секундах, 0 - без лимита
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    type = relationship("QuestionType", back_populates="questions")
    test_questions = relationship("TestQuestion", back_populates="question", cascade="all, delete-orphan")
    user_answers = relationship("UserAnswer", back_populates="question")
