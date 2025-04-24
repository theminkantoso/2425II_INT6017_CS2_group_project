from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main.models.image_cache import ImageCacheModel


async def get_cached_image(
    session: AsyncSession, input_hash: str
) -> ImageCacheModel | None:
    stmt = select(ImageCacheModel).where(ImageCacheModel.hash_id == input_hash)
    stmt = stmt.where(ImageCacheModel.is_deleted.is_(False))
    result = await session.execute(stmt)
    return result.scalars().first()
