from pydantic import BaseModel


class ImageMetadata(BaseModel):
    filename: str | None = None
    hash: str
    image_bytes: bytes
    file_url: str | None = None
