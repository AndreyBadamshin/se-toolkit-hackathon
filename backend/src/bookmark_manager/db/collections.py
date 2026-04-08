from sqlmodel import select, col
from sqlalchemy.ext.asyncio import AsyncSession

from bookmark_manager.models.collection import Collection


async def get_collections_by_user(
    session: AsyncSession, user_id: int, skip: int = 0, limit: int = 50
) -> list[Collection]:
    statement = (
        select(Collection)
        .where(Collection.user_id == user_id)
        .order_by(col(Collection.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_collection_by_id(
    session: AsyncSession, collection_id: int, user_id: int
) -> Collection | None:
    statement = select(Collection).where(
        Collection.id == collection_id,
        Collection.user_id == user_id,
    )
    result = await session.execute(statement)
    return result.scalars().first()


async def create_collection(session: AsyncSession, collection: Collection) -> Collection:
    session.add(collection)
    await session.commit()
    await session.refresh(collection)
    return collection


async def update_collection(session: AsyncSession, collection: Collection) -> Collection:
    session.add(collection)
    await session.commit()
    await session.refresh(collection)
    return collection


async def delete_collection(session: AsyncSession, collection: Collection) -> None:
    await session.delete(collection)
    await session.commit()


async def add_bookmark_to_collection(
    session: AsyncSession, bookmark_id: int, collection_id: int
) -> None:
    from bookmark_manager.models.bookmark_collection import BookmarkCollection
    
    bookmark_collection = BookmarkCollection(
        bookmark_id=bookmark_id,
        collection_id=collection_id,
    )
    session.add(bookmark_collection)
    await session.commit()


async def remove_bookmark_from_collection(
    session: AsyncSession, bookmark_id: int, collection_id: int
) -> None:
    from bookmark_manager.models.bookmark_collection import BookmarkCollection
    
    statement = select(BookmarkCollection).where(
        BookmarkCollection.bookmark_id == bookmark_id,
        BookmarkCollection.collection_id == collection_id,
    )
    result = await session.execute(statement)
    bookmark_collection = result.scalars().first()
    if bookmark_collection:
        await session.delete(bookmark_collection)
        await session.commit()


async def get_collections_for_bookmark(
    session: AsyncSession, bookmark_id: int, user_id: int
) -> list[Collection]:
    from bookmark_manager.models.bookmark_collection import BookmarkCollection
    
    statement = (
        select(Collection)
        .join(BookmarkCollection, Collection.id == BookmarkCollection.collection_id)
        .where(
            BookmarkCollection.bookmark_id == bookmark_id,
            Collection.user_id == user_id,
        )
    )
    result = await session.execute(statement)
    return list(result.scalars().all())
