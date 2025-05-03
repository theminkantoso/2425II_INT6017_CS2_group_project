from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends

from main._db import get_db_session
from main._redis import get_redis
from main.libs import image_lib
from main.misc.utils import hashing
from main._rabbit import rabbit_connection
from main.schemas.image import ImageMetadata, ImageRequest
from main.services import gcs_service

router: APIRouter = APIRouter()
UPLOAD_FOLDER = Path("/storage")
UPLOAD_FOLDER.mkdir(exist_ok=True)


@router.post("/api/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    cache_connection=Depends(get_redis),
    session=Depends(get_db_session),
):
    # TODO: Validate image type and size
    # Store image to folder storage and return 200

    # Image hash
    image_bytes = await file.read()
    image_hash = hashing.calculate_image_hash(file_bytes=image_bytes)

    # Check if the image already exists in the cache
    pdf_url_cache = await cache_connection.get(image_hash)
    if pdf_url_cache:
        # If the image already exists in the cache, return the cached image
        # TODO: Handle return pdf file url
        return {"message": "Image already exists", "pdf_url": pdf_url_cache}
    else:
        pdf_url_cache = await image_lib.handle_cache_miss(
            session=session,
            image_metadata=ImageMetadata(
                filename=file.filename, image_bytes=image_bytes, hash=image_hash
            ),
            upload_folder=UPLOAD_FOLDER,
            rabbit_connection=rabbit_connection,
            cache_connection=cache_connection,
        )
        if pdf_url_cache:
            return {"message": "Image already exists", "pdf_url": pdf_url_cache}


@router.post("/api/handle-image")
async def handle_image(
    image_request: ImageRequest,
    cache_connection=Depends(get_redis),
    session=Depends(get_db_session),
):
    # Get file from GCS
    image_bytes = await gcs_service.download_image_from_gcs_to_memory(
        public_url=image_request.file_url
    )

    # Image hash
    image_hash = hashing.calculate_image_hash(file_bytes=image_bytes)

    # Check if the image already exists in the cache
    pdf_url_cache = await cache_connection.get(image_hash)
    if pdf_url_cache:
        # If the image already exists in the cache, return the cached image
        # TODO: Handle return pdf file url
        return {"message": "Image already exists", "pdf_url": pdf_url_cache}
    else:
        pdf_url_cache = await image_lib.handle_cache_miss(
            session=session,
            image_metadata=ImageMetadata(
                file_url=image_request.file_url,
                image_bytes=image_bytes,
                hash=image_hash,
            ),
            rabbit_connection=rabbit_connection,
            cache_connection=cache_connection,
        )
        if pdf_url_cache:
            return {"message": "Image already exists", "pdf_url": pdf_url_cache}
