from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends

from main._db import get_db_session
from main._redis import get_redis
from main.libs import image_lib
from main.misc.utils import hashing
from main._rabbit import rabbit_connection
from main.schemas.image import ImageMetadata

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
        )
        if pdf_url_cache:
            return {"message": "Image already exists", "pdf_url": pdf_url_cache}

    # try:
    #     # Generate a unique filename
    #     file_extension = file.filename.split(".")[-1]
    #     unique_filename = f"{uuid.uuid4()}.{file_extension}"
    #
    #     # Initialize GCS client
    #     storage_client = storage.Client()
    #     bucket = storage_client.bucket("your-bucket-name")
    #     blob = bucket.blob(f"images/{unique_filename}")
    #
    #     # Read file content
    #     contents = await file.read()
    #
    #     # Upload to GCS
    #     blob.upload_from_string(contents, content_type=file.content_type)
    #
    #     # Generate public URL (if your bucket allows public access)
    #     image_url = (
    #         f"https://storage.googleapis.com/your-bucket-name/images/{unique_filename}"
    #     )
    #
    #     return {"success": True, "filename": unique_filename, "image_url": image_url}
    # except Exception as e:
    #     raise InternalServerError(error_message=str(e))
