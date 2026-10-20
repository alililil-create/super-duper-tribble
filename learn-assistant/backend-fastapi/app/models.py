from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    level: Mapped[str] = mapped_column(String(20), default="B1")
    source: Mapped[str] = mapped_column(String(200), default="user_upload")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    scenes: Mapped[list["Scene"]] = relationship(back_populates="article", cascade="all, delete-orphan")

class Scene(Base):
    __tablename__ = "scenes"
    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    user_role: Mapped[str] = mapped_column(String(100))
    goal: Mapped[str] = mapped_column(Text)
    ai_roles: Mapped[list] = mapped_column(JSON)
    conflict: Mapped[str] = mapped_column(Text)
    task_chain: Mapped[list] = mapped_column(JSON)
    language_goals: Mapped[str] = mapped_column(Text)
    final_output: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    article: Mapped[Article] = relationship(back_populates="scenes")

class LearningSession(Base):
    __tablename__ = "sessions"
    # Stage 3 has only active sessions. This also prevents concurrent duplicate creation.
    __table_args__ = (UniqueConstraint("user_id", "scene_id", name="uq_user_scene"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))
    scene_id: Mapped[int] = mapped_column(ForeignKey("scenes.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    messages: Mapped[list["Message"]] = relationship(back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    session: Mapped[LearningSession] = relationship(back_populates="messages")
