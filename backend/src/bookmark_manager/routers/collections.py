from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from bookmark_manager.database import get_session
from bookmark_manager.models.user import User
from bookmark_manager.models.collection import (
    Collection,
    CollectionCreate,
    CollectionResponse,
    CollectionUpdate,
)
from bookmark_manager.auth import get_current_user
from bookmark_manager.db import collections as db_collections
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection_data: CollectionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    collection = Collection(
        name=collection_data.name,
        color=collection_data.color,
        user_id=current_user.id,
    )
    collection = await db_collections.create_collection(session, collection)
    return collection


@router.get("", response_model=list[CollectionResponse])
async def list_collections(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await db_collections.get_collections_by_user(
        session, current_user.id, skip=skip, limit=limit
    )


@router.get("/{collection_id}", response_model=CollectionResponse)
async def get_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    collection = await db_collections.get_collection_by_id(
        session, collection_id, current_user.id
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: int,
    update_data: CollectionUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    collection = await db_collections.get_collection_by_id(
        session, collection_id, current_user.id
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(collection, key, value)

    collection = await db_collections.update_collection(session, collection)
    return collection


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    collection = await db_collections.get_collection_by_id(
        session, collection_id, current_user.id
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    await db_collections.delete_collection(session, collection)


@router.post("/{collection_id}/bookmarks/{bookmark_id}", status_code=status.HTTP_201_CREATED)
async def add_bookmark_to_collection(
    collection_id: int,
    bookmark_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a bookmark to a collection."""
    # Verify ownership
    collection = await db_collections.get_collection_by_id(
        session, collection_id, current_user.id
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    from bookmark_manager.db import bookmarks as db_bookmarks
    bookmark = await db_bookmarks.get_bookmark_by_id(
        session, bookmark_id, current_user.id
    )
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    await db_collections.add_bookmark_to_collection(
        session, bookmark_id, collection_id
    )
    return {"message": "Bookmark added to collection"}


@router.delete("/{collection_id}/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bookmark_from_collection(
    collection_id: int,
    bookmark_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove a bookmark from a collection."""
    collection = await db_collections.get_collection_by_id(
        session, collection_id, current_user.id
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    await db_collections.remove_bookmark_from_collection(
        session, bookmark_id, collection_id
    )


@router.get("/{collection_id}/bookmarks", response_model=list)
async def get_bookmarks_in_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get all bookmarks in a collection."""
    from bookmark_manager.models.bookmark import Bookmark
    from bookmark_manager.models.bookmark_collection import BookmarkCollection
    
    collection = await db_collections.get_collection_by_id(
        session, collection_id, current_user.id
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    statement = (
        select(Bookmark)
        .join(BookmarkCollection, Bookmark.id == BookmarkCollection.bookmark_id)
        .where(BookmarkCollection.collection_id == collection_id)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())
