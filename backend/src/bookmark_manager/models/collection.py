from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class CollectionBase(SQLModel):
    name: str
    color: str = "#007bff"


class Collection(CollectionBase, table=True):
    __tablename__ = "collections"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CollectionCreate(SQLModel):
    name: str
    color: str = "#007bff"


class CollectionResponse(CollectionBase):
    id: int
    user_id: int
    created_at: datetime


class CollectionUpdate(SQLModel):
    name: Optional[str] = None
    color: Optional[str] = None
