from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from bookmark_manager.database import get_session
from bookmark_manager.models.user import User
from bookmark_manager.models.bookmark import Bookmark, BookmarkCreate, BookmarkResponse, BookmarkUpdate
from bookmark_manager.auth import get_current_user
from bookmark_manager.db import bookmarks as db_bookmarks
from bookmark_manager.llm_service import fetch_page_metadata, analyze_with_llm

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


@router.post("", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Fetch page metadata
    metadata = await fetch_page_metadata(bookmark_data.url)

    # Analyze with LLM
    analysis = await analyze_with_llm(metadata)

    # Create bookmark
    bookmark = Bookmark(
        url=bookmark_data.url,
        title=analysis["title"],
        summary=analysis["summary"],
        tags=analysis["tags"],
        category=analysis["category"],
        image_url=metadata.get("og_image"),
        user_id=current_user.id,
    )

    bookmark = await db_bookmarks.create_bookmark(session, bookmark)
    return bookmark


@router.get("", response_model=list[BookmarkResponse])
async def list_bookmarks(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await db_bookmarks.get_bookmarks_by_user(session, current_user.id, skip=skip, limit=limit)


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    bookmark = await db_bookmarks.get_bookmark_by_id(session, bookmark_id, current_user.id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return bookmark


@router.put("/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(
    bookmark_id: int,
    update_data: BookmarkUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    bookmark = await db_bookmarks.get_bookmark_by_id(session, bookmark_id, current_user.id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(bookmark, key, value)

    bookmark = await db_bookmarks.update_bookmark(session, bookmark)
    return bookmark


@router.delete("/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    bookmark = await db_bookmarks.get_bookmark_by_id(session, bookmark_id, current_user.id)
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    await db_bookmarks.delete_bookmark(session, bookmark)
