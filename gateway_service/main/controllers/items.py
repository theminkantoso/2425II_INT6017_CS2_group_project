import logging

from fastapi import APIRouter, Request

from main.services.items import count_items


router: APIRouter = APIRouter()


@router.get("/items/count")
async def get_items_count():
    count = await count_items()

    return {
        "count": count,
    }


@router.post("/items")
async def _add_item(request: Request):
    # await add_item()
    origin = request.headers.get("origin", "Unknown")
    logging.warning(f"Request body {str(await request.json())}, origin {str(origin)}")
    return {}
