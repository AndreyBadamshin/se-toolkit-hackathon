import csv
import io
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from bookmark_manager.database import get_session
from bookmark_manager.models.user import User
from bookmark_manager.models.bookmark import Bookmark
from bookmark_manager.auth import get_current_user
from bookmark_manager.db import bookmarks as db_bookmarks
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import-export", tags=["import-export"])


@router.get("/export/json")
async def export_bookmarks_json(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Export bookmarks to JSON."""
    bookmarks = await db_bookmarks.get_bookmarks_by_user(session, current_user.id, limit=10000)
    
    data = [
        {
            "url": b.url,
            "title": b.title,
            "summary": b.summary,
            "categories": b.categories,
            "image_url": b.image_url,
            "created_at": b.created_at.isoformat(),
        }
        for b in bookmarks
    ]
    
    return {"bookmarks": data, "count": len(data)}


@router.get("/export/csv")
async def export_bookmarks_csv(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Export bookmarks to CSV."""
    bookmarks = await db_bookmarks.get_bookmarks_by_user(session, current_user.id, limit=10000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["url", "title", "summary", "categories", "image_url", "created_at"])
    
    for b in bookmarks:
        writer.writerow([
            b.url,
            b.title,
            b.summary,
            ",".join(b.categories),
            b.image_url or "",
            b.created_at.isoformat(),
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bookmarks.csv"},
    )


@router.post("/import/csv", status_code=201)
async def import_bookmarks_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Import bookmarks from CSV."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    text_content = content.decode("utf-8")
    
    reader = csv.DictReader(io.StringIO(text_content))
    imported = 0
    
    for row in reader:
        try:
            categories = row.get("categories", "")
            categories_list = [c.strip() for c in categories.split(",") if c.strip()] if categories else []
            
            bookmark = Bookmark(
                url=row["url"],
                title=row.get("title", "Untitled"),
                summary=row.get("summary", ""),
                categories=categories_list,
                image_url=row.get("image_url") or None,
                user_id=current_user.id,
            )
            await db_bookmarks.create_bookmark(session, bookmark)
            imported += 1
        except Exception as e:
            logger.error(f"Failed to import bookmark: {e}")
            continue
    
    return {"message": f"Successfully imported {imported} bookmarks", "count": imported}
