from main._rabbit import rabbit_connection
from main.enums import RabbitMessageType
from main.models.retry_job import RetryJobModel
from sqlalchemy.ext.asyncio import AsyncSession

from main.schemas.message import MessageSchema
from main.services import retry_job_service


async def retry_ocr():
    pass


async def retry_translate(job: RetryJobModel):
    message = MessageSchema(
        type=RabbitMessageType.FILE_UPLOADED,
        file_path=job.file_path,
        image_hash=job.image_hash,
        encoded_text=job.encoded_text,
        text_to_translate=job.text_to_translate,
        job_id=job.id,
    )
    await rabbit_connection.send_messages(messages=message.model_dump())


async def retry_pdf(job: RetryJobModel):
    pass


async def retry_failed_jobs(session: AsyncSession):
    failed_jobs = await retry_job_service.get_failed_jobs(session)
    for job in failed_jobs:
        match job.step:
            case 1:
                await retry_ocr()
            case 2:
                await retry_translate(job=job)
            case 3:
                await retry_pdf()
            case _:
                pass
