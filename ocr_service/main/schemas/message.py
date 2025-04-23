from pydantic import BaseModel


class MessageSchema(BaseModel):
    type: str
    file_path: str
    image_hash: str
    encoded_text: str | None = None
