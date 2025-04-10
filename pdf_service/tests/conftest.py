import asyncio
import sys

import pytest
from httpx import AsyncClient

from main import app, config, db
from main.libs.log import get_logger
from main.models.base import BaseModel


logger = get_logger(__name__)

if config.ENVIRONMENT != "test":
    logger.error('Tests must be run with "ENVIRONMENT=test"')
    sys.exit(1)


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()

    yield loop

    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def recreate_database():
    async with db.engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)


@pytest.fixture(scope="function", autouse=True)
async def database():
    connection = await db.engine.connect()
    transaction = await connection.begin()

    db.session_factory.configure(bind=connection)
    db.scoped_session()

    yield

    await db.scoped_session.remove()
    await transaction.rollback()
    await connection.close()


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
