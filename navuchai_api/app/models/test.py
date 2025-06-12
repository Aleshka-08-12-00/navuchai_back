from sqlalchemy import Integer, String, Column, TIMESTAMP, ForeignKey, Boolean, Enum, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
import enum


class TestAccessEnum(str, enum.Enum):
    PUBLIC = 'public'
    PRIVATE = 'private'


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
    thumbnail_id = Column(Integer, ForeignKey('file.id', ondelete='SET NULL'), nullable=True)
    avg_percent = Column(Integer, nullable=True, default=0)
    completed_number = Column(Integer, nullable=True, default=0)
    welcome_message = Column(String(255), nullable=True)
    goodbye_message = Column(String(255), nullable=True)
    access = Column(Enum(TestAccessEnum, name='test_access_enum', create_type=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=TestAccessEnum.PRIVATE)
    code = Column(String, nullable=True, server_default=text("encode(gen_random_bytes(16), 'base64')"))
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    category = relationship("Category", back_populates="tests", single_parent=True)
    creator = relationship("User", back_populates="created_tests")
    test_questions = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="test", cascade="all, delete-orphan")
    locale = relationship("Locale", back_populates="tests")
    image = relationship("File", foreign_keys=[img_id], lazy="selectin")
    thumbnail = relationship("File", foreign_keys=[thumbnail_id], lazy="selectin")
    status = relationship("TestStatus", back_populates="tests")
    test_accesses = relationship("TestAccess", back_populates="test", cascade="all, delete-orphan")
