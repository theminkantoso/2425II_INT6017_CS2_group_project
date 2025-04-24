import uuid

from fastapi import APIRouter, UploadFile, File
from google.cloud import storage
from main.misc.exceptions import InternalServerError

router: APIRouter = APIRouter()


@router.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Generate a unique filename
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Initialize GCS client
        storage_client = storage.Client()
        bucket = storage_client.bucket("your-bucket-name")
        blob = bucket.blob(f"images/{unique_filename}")

        # Read file content
        contents = await file.read()

        # Upload to GCS
        blob.upload_from_string(contents, content_type=file.content_type)

        # Generate public URL (if your bucket allows public access)
        image_url = (
            f"https://storage.googleapis.com/your-bucket-name/images/{unique_filename}"
        )

        return {"success": True, "filename": unique_filename, "image_url": image_url}
    except Exception as e:
        raise InternalServerError(error_message=str(e))
