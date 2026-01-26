from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base

topic_tags = Table(
    "topic_tags",
    Base.metadata,
    Column("topic_id", Integer, ForeignKey("topic.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("topic_tag.id", ondelete="CASCADE"), primary_key=True),
)

topic_files = Table(
    "topic_files",
    Base.metadata,
    Column("topic_id", Integer, ForeignKey("topic.id", ondelete="CASCADE"), primary_key=True),
    Column("file_id", Integer, ForeignKey("file.id", ondelete="CASCADE"), primary_key=True),
)


class Topic(Base):
    __tablename__ = "topic"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tags = relationship("TopicTag", secondary=topic_tags, back_populates="topics", lazy="selectin")
    files = relationship("File", secondary=topic_files, lazy="selectin")


class TopicTag(Base):
    __tablename__ = "topic_tag"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    topics = relationship("Topic", secondary=topic_tags, back_populates="tags", lazy="selectin")
