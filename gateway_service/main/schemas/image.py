from pydantic import BaseModel


class ImageMetadata(BaseModel):
    filename: str
    hash: str
    image_bytes: bytes
