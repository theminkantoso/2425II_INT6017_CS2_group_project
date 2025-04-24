from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from main._config import config
from ._rabbit import rabbit_connection
from .middlewares import AccessLogMiddleware, DBSessionMiddleware

api_docs_enabled = config.ENVIRONMENT == "local"


@asynccontextmanager
async def lifespan(_: FastAPI):
    await rabbit_connection.connect()
    yield
    await rabbit_connection.disconnect()


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
