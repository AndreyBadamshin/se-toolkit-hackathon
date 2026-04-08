from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from bookmark_manager.database import get_session
from bookmark_manager.models.user import User
from bookmark_manager.models.bookmark import (
    Bookmark,
    BookmarkCreate,
    BookmarkResponse,
    BookmarkUpdate,
)
from bookmark_manager.auth import get_current_user
from bookmark_manager.db import bookmarks as db_bookmarks
from bookmark_manager.llm_service import fetch_page_metadata, analyze_with_llm, generate_embedding
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


class CategoryUpdate(BaseModel):
    categories: list[str]


class CategoryAdd(BaseModel):
    category: str


@router.post("", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    logger.info(f"Creating bookmark for URL: {bookmark_data.url}")

    # Fetch page metadata
    metadata = await fetch_page_metadata(bookmark_data.url)

    # Analyze with LLM
    try:
        analysis = await analyze_with_llm(metadata)
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        if "credentials" in str(e).lower() or "auth" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="LLM service authentication failed. Please re-authenticate with Qwen CLI and restart the qwen-code-api container.",
            )
        raise HTTPException(status_code=503, detail=f"LLM analysis failed: {str(e)}")

    logger.info(f"LLM analysis result: {analysis}")

    # Create bookmark
    bookmark = Bookmark(
        url=bookmark_data.url,
        title=analysis["title"],
        summary=analysis["summary"],
        categories=analysis.get("categories", []),
        image_url=metadata.get("og_image"),
        user_id=current_user.id,
    )

    # Generate embedding for search
    embedding_text = f"{bookmark.title} {bookmark.summary} {' '.join(bookmark.categories)}"
    bookmark.embedding = await generate_embedding(embedding_text)

    bookmark = await db_bookmarks.create_bookmark(session, bookmark)
    return bookmark


@router.get("", response_model=list[BookmarkResponse])
async def list_bookmarks(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await db_bookmarks.get_bookmarks_by_user(
        session, current_user.id, skip=skip, limit=limit
    )


@router.get("/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(
    bookmark_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    bookmark = await db_bookmarks.get_bookmark_by_id(
        session, bookmark_id, current_user.id
    )
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
    bookmark = await db_bookmarks.get_bookmark_by_id(
        session, bookmark_id, current_user.id
    )
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
    bookmark = await db_bookmarks.get_bookmark_by_id(
        session, bookmark_id, current_user.id
    )
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    await db_bookmarks.delete_bookmark(session, bookmark)


@router.put("/{bookmark_id}/categories", response_model=BookmarkResponse)
async def update_categories(
    bookmark_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update all categories for a bookmark (max 5)."""
    bookmark = await db_bookmarks.get_bookmark_by_id(
        session, bookmark_id, current_user.id
    )
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    # Limit to 5 categories
    bookmark.categories = category_data.categories[:5]
    bookmark = await db_bookmarks.update_bookmark(session, bookmark)
    return bookmark


@router.post("/{bookmark_id}/categories", response_model=BookmarkResponse)
async def add_category(
    bookmark_id: int,
    category_data: CategoryAdd,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a single category to a bookmark (max 5 total)."""
    bookmark = await db_bookmarks.get_bookmark_by_id(
        session, bookmark_id, current_user.id
    )
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    # Check if category already exists
    if category_data.category in bookmark.categories:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    # Check if we've reached the limit
    if len(bookmark.categories) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 categories reached")

    bookmark.categories.append(category_data.category)
    flag_modified(bookmark, "categories")
    bookmark = await db_bookmarks.update_bookmark(session, bookmark)
    return bookmark


@router.delete("/{bookmark_id}/categories/{category}", response_model=BookmarkResponse)
async def remove_category(
    bookmark_id: int,
    category: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove a single category from a bookmark."""
    bookmark = await db_bookmarks.get_bookmark_by_id(
        session, bookmark_id, current_user.id
    )
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    if category not in bookmark.categories:
        raise HTTPException(status_code=404, detail="Category not found")

    bookmark.categories.remove(category)
    flag_modified(bookmark, "categories")
    bookmark = await db_bookmarks.update_bookmark(session, bookmark)
    return bookmark
