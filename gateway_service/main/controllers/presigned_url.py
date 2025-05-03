from fastapi import APIRouter, UploadFile, File

from main.libs import image_lib

router: APIRouter = APIRouter()


@router.post("/api/presigned-url")
async def generate_presigned_url(
    file: UploadFile = File(...),
):

    gcs_presigned_url = await image_lib.generate_presigned_url(
        file_name=file.filename,
    )
    return {"upload_status": 301, "gcs_presigned_url": gcs_presigned_url}
