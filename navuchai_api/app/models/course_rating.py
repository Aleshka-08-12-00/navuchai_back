from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class CourseRating(Base):
    __tablename__ = "course_rating"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    course = relationship("Course", back_populates="ratings")
    user = relationship("User", back_populates="course_ratings")

    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name="course_user_rating_unique"),
    )
