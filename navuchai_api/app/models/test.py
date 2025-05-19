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
    status_id = Column(Integer, ForeignKey("test_status.id"), nullable=False)
    frozen = Column(Boolean, nullable=False)
    locale_id = Column(Integer, ForeignKey('locale.id'), nullable=False)
    img_id = Column(Integer, ForeignKey('file.id', ondelete='SET NULL'), nullable=True)
    avg_percent = Column(Integer, nullable=True, default=50)
    completed_number = Column(Integer, nullable=True, default=40)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    category = relationship("Category", back_populates="tests", single_parent=True)
    creator = relationship("User", back_populates="created_tests")
    test_questions = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="test")
    locale = relationship("Locale", back_populates="tests")
    image = relationship("File", foreign_keys=[img_id])
    status = relationship("TestStatus", back_populates="tests")
    test_accesses = relationship("TestAccess", back_populates="test", cascade="all, delete-orphan")
