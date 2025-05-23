from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from main.models.retry_job import RetryJobModel


async def create_retry_job(session: AsyncSession, data: dict) -> RetryJobModel:
    retry_job = RetryJobModel(**data)
    session.add(retry_job)
    await session.commit()
    return retry_job


async def get_failed_jobs_ids_and_steps(session: AsyncSession) -> list[tuple[int, int]]:
    stmt = select(RetryJobModel.id, RetryJobModel.step)
    stmt = stmt.where(RetryJobModel.is_deleted.is_(False))
    result = await session.execute(stmt)
    return list(result.all())
