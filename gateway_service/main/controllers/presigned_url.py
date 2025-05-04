from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends

from main._db import get_db_session
from main._redis import get_redis
from main.libs import image_lib
from main.misc.utils import hashing
from main.schemas.image import ImageMetadata

router: APIRouter = APIRouter()
UPLOAD_FOLDER = Path("/storage")
UPLOAD_FOLDER.mkdir(exist_ok=True)


@router.post("/api/presigned-url")
async def generate_presigned_url(
    file: UploadFile = File(...),
    cache_connection=Depends(get_redis),
    session=Depends(get_db_session),
):
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
        pdf_url_cache = await image_lib.check_cache_from_db(
            session=session,
            image_metadata=ImageMetadata(
                filename=file.filename, image_bytes=image_bytes, hash=image_hash
            ),
            cache_connection=cache_connection,
        )
        if pdf_url_cache:
            return {"message": "Image already exists", "pdf_url": pdf_url_cache}

    gcs_presigned_url, job_uuid = await image_lib.generate_presigned_url(
        file_name=file.filename,
    )
    return {
        "upload_status": 301,
        "gcs_presigned_url": gcs_presigned_url,
        "job_uuid": job_uuid,
    }
