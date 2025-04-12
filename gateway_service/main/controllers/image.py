import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File
import os

from main._rabbit import rabbit_connection
from main.enums import RabbitMessageType
from main.misc.exceptions import InternalServerError

router: APIRouter = APIRouter()
UPLOAD_FOLDER = Path("/storage")
UPLOAD_FOLDER.mkdir(exist_ok=True)


@router.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...)):
    # TODO: Validate image type and size
    # Store image to folder storage and return 200
    try:
        filename = uuid.uuid4().hex + "." + file.filename.split(".")[-1]

        # Save the uploaded file to the storage directory
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        message = {"type": RabbitMessageType.FILE_UPLOADED, "file_path": file_path}
        await rabbit_connection.send_messages(messages=message)
        return {"success": True, "filename": file.filename, "file_path": file_path}
    except Exception as e:
        raise InternalServerError(error_message=str(e))

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
