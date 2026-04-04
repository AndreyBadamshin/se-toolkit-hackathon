from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB


class BookmarkBase(SQLModel):
    url: str
    title: str
    summary: str
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSONB))
    category: str = "other"
    image_url: Optional[str] = None


class Bookmark(BookmarkBase, table=True):
    __tablename__ = "bookmarks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BookmarkCreate(SQLModel):
    url: str


class BookmarkResponse(BookmarkBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class BookmarkUpdate(SQLModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[list[str]] = None
    category: Optional[str] = None
