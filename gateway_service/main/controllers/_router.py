# mypy: ignore-errors

from fastapi import APIRouter

from . import items, probe, image

router = APIRouter()

router.include_router(probe.router, tags=["probe"])
router.include_router(items.router, tags=["items"])
router.include_router(image.router, tags=["image"])
