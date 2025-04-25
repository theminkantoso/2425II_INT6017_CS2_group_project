from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ._config import config
from ._rabbit import rabbit_connection
from .middlewares import AccessLogMiddleware, DBSessionMiddleware
from ._redis import redis

api_docs_enabled = config.ENVIRONMENT == "local"


# Cron scheduler
scheduler = AsyncIOScheduler()
trigger = CronTrigger(hour=0, minute=0)

# scheduler.add_job(
#     cron_transaction_lib.update_fraud_prediction_transactions,
#     trigger=trigger,
#     kwargs={"ml_model_path": config.ML_MODEL_PATH},
# )
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
