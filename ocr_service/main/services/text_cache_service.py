from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main.models.text_cache import TextCacheModel


async def get_cached_image(
    session: AsyncSession, input_text: str
) -> TextCacheModel | None:
    stmt = select(TextCacheModel).where(TextCacheModel.text_encode == input_text)
    stmt = stmt.where(TextCacheModel.is_deleted.is_(False))
    result = await session.execute(stmt)
    return result.scalars().first()
