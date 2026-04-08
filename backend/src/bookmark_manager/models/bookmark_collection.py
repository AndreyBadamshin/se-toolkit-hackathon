from sqlmodel import SQLModel, Field
from typing import Optional


class BookmarkCollection(SQLModel, table=True):
    __tablename__ = "bookmark_collections"

    bookmark_id: int = Field(foreign_key="bookmarks.id", primary_key=True, ondelete="CASCADE")
    collection_id: int = Field(foreign_key="collections.id", primary_key=True, ondelete="CASCADE")
