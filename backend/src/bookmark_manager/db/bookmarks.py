from datetime import datetime

from sqlmodel import select, col
from sqlalchemy.ext.asyncio import AsyncSession

from bookmark_manager.models.bookmark import Bookmark


async def get_bookmarks_by_user(
    session: AsyncSession, user_id: int, skip: int = 0, limit: int = 50
) -> list[Bookmark]:
    statement = (
        select(Bookmark)
        .where(Bookmark.user_id == user_id)
        .order_by(col(Bookmark.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_bookmark_by_id(
    session: AsyncSession, bookmark_id: int, user_id: int
) -> Bookmark | None:
    statement = select(Bookmark).where(
        Bookmark.id == bookmark_id,
        Bookmark.user_id == user_id,
    )
    result = await session.execute(statement)
    return result.scalars().first()


async def create_bookmark(session: AsyncSession, bookmark: Bookmark) -> Bookmark:
    session.add(bookmark)
    await session.commit()
    await session.refresh(bookmark)
    return bookmark


async def update_bookmark(session: AsyncSession, bookmark: Bookmark) -> Bookmark:
    bookmark.updated_at = datetime.utcnow()
    session.add(bookmark)
    await session.commit()
    await session.refresh(bookmark)
    return bookmark


async def delete_bookmark(session: AsyncSession, bookmark: Bookmark) -> None:
    await session.delete(bookmark)
    await session.commit()
