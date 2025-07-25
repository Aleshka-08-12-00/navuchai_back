from sqlalchemy import Integer, Column, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Result(Base):
    __tablename__ = 'result'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    score = Column(Integer, nullable=True)
    result = Column(JSONB, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="results")
    test = relationship("Test", back_populates="results")
    user_answers = relationship(
        "UserAnswer",
        back_populates="result",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=True
    )
