from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from bookmark_manager.database import get_session
from bookmark_manager.models.user import User
from bookmark_manager.auth import get_current_user
from bookmark_manager.llm_service import search_bookmarks_with_llm
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search_bookmarks(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Search bookmarks using LLM-based natural language search."""
    try:
        # Fetch all user's bookmarks to send to LLM
        statement = text("""
            SELECT b.id, b.url, b.title, b.summary, b.categories, b.image_url, b.created_at, b.updated_at, b.user_id
            FROM bookmarks b
            WHERE b.user_id = :user_id
            ORDER BY b.created_at DESC
            LIMIT :limit
        """)
        result = await session.execute(
            statement,
            {"user_id": current_user.id, "limit": limit}
        )
        rows = result.fetchall()
        
        if not rows:
            return []
        
        # Prepare bookmarks for LLM
        bookmarks_for_llm = [
            {
                "id": row.id,
                "url": row.url,
                "title": row.title,
                "summary": row.summary,
                "categories": row.categories if row.categories else [],
            }
            for row in rows
        ]
        
        # Use LLM to find relevant bookmarks
        relevant_ids = await search_bookmarks_with_llm(q, bookmarks_for_llm)
        
        if not relevant_ids:
            return []
        
        # Fetch the relevant bookmarks by IDs
        placeholders = ", ".join([f":id_{i}" for i in range(len(relevant_ids))])
        params = {f"id_{i}": relevant_ids[i] for i in range(len(relevant_ids))}
        params["user_id"] = current_user.id
        
        statement = text(f"""
            SELECT b.id, b.url, b.title, b.summary, b.categories, b.image_url, b.created_at, b.updated_at, b.user_id
            FROM bookmarks b
            WHERE b.user_id = :user_id
              AND b.id IN ({placeholders})
            ORDER BY b.created_at DESC
        """)
        result = await session.execute(statement, params)
        filtered_rows = result.fetchall()
        
        return [
            {
                "id": row.id,
                "url": row.url,
                "title": row.title,
                "summary": row.summary,
                "categories": row.categories,
                "image_url": row.image_url,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "user_id": row.user_id,
            }
            for row in filtered_rows
        ]

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
