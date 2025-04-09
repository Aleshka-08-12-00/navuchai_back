from sqlalchemy import Integer, String, Column, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Question(Base):
    __tablename__ = 'question'

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    text_abstract = Column(String, nullable=False)
    type = Column(String, nullable=False)
    reviewable = Column(Boolean, nullable=False)
    answers = Column(JSONB, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    test_questions = relationship("TestQuestion", back_populates="question", cascade="all, delete-orphan")
    user_answers = relationship("UserAnswer", back_populates="question")
