from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main.models.image_cache import ImageCache


async def get_cached_image(session: AsyncSession, input_hash: str) -> ImageCache | None:
    stmt = select(ImageCache).where(ImageCache.hash_id == input_hash)
    stmt = stmt.where(ImageCache.is_deleted.is_(False))
    result = await session.execute(stmt)
    return result.scalars().first()
