from sqlalchemy import Integer, Column, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class UserAnswer(Base):
    __tablename__ = 'user_answer'

    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey('result.id', ondelete='CASCADE'), nullable=False)
    question_id = Column(Integer, ForeignKey('question.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    answer = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    result = relationship("Result", back_populates="user_answers", lazy="joined")
    question = relationship("Question", back_populates="user_answers")
    user = relationship("User", back_populates="user_answers")
