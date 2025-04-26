from main import config
from main._db import get_db_session
from main._rabbit import rabbit_connection
from main.services import retry_job_service


# TODO: Cron cleanup invalid jobs
async def retry_failed_jobs():
    async for session in get_db_session():
        failed_jobs = await retry_job_service.get_failed_jobs_ids_and_steps(session)
        step_one_failed_ids, step_two_failed_ids, step_three_failed_ids = [], [], []

        for job_id, step in failed_jobs:
            match step:
                case 1:
                    step_one_failed_ids.append(job_id)
                case 2:
                    step_two_failed_ids.append(job_id)
                case 3:
                    step_three_failed_ids.append(job_id)
                case _:
                    pass

        if step_one_failed_ids:
            await rabbit_connection.send_messages(
                messages={"job_ids": step_one_failed_ids},
                routing_key=config.RABBITMQ_QUEUE_GATEWAY_TO_OCR,
            )

        if step_two_failed_ids:
            await rabbit_connection.send_messages(
                messages={"job_ids": step_two_failed_ids},
                routing_key=config.RABBITMQ_QUEUE_OCR_TO_TRANSLATE,
            )

        if step_three_failed_ids:
            await rabbit_connection.send_messages(
                messages={"job_ids": step_three_failed_ids},
                routing_key=config.RABBITMQ_QUEUE_TRANSLATE_TO_PDF,
            )
