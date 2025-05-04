from contextlib import asynccontextmanager

import sentry_sdk
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ._config import config
from ._rabbit import rabbit_connection
from .libs.cron_libs import retry_lib
from .middlewares import AccessLogMiddleware, DBSessionMiddleware
from ._redis import redis

api_docs_enabled = config.ENVIRONMENT == "local"


# Cron scheduler
scheduler = AsyncIOScheduler()
trigger = CronTrigger(minute="*")

scheduler.add_job(
    retry_lib.retry_failed_jobs,
    trigger=trigger,
)
scheduler.start()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Setup phase
    await redis.ping()
    await rabbit_connection.connect()
    try:
        yield
    finally:
        # Teardown phase
        await redis.close()
        await rabbit_connection.disconnect()
        scheduler.shutdown()


sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)
app = FastAPI(
    redoc_url=None, docs_url="/docs" if api_docs_enabled else None, lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(DBSessionMiddleware)
app.add_middleware(AccessLogMiddleware)
