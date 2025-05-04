from fastapi import APIRouter

from main._rabbit import rabbit_connection

router = APIRouter()


@router.get("/pings")
async def ping():
    message = {"type": "test_message", "message": "Test message text"}
    await rabbit_connection.send_messages(messages=message)
    return {}


@router.get("/ready")
async def is_ready():
    return {}


@router.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0
