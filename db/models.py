import uuid
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hashed_password = Column(String, nullable=False)
    tasks = relationship("Task", backref="user")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    title = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.now())
    tag_id = Column(Integer, ForeignKey("tags.id"))
    tags = relationship("Tag", backref="tasks")



class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    tag = Column(String, index=True, unique=True)
