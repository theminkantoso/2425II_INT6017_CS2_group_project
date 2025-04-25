from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main.models.retry_job import RetryJobModel


async def create_retry_job(
    session: AsyncSession, data: dict
) -> RetryJobModel:
    retry_job = RetryJobModel(**data)
    session.add(retry_job)
    await session.commit()
    return retry_job



