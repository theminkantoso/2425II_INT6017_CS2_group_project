from pydantic import BaseModel


class MessageSchema(BaseModel):
    type: str | None = None
    file_url: str
    image_hash: str
    encoded_text: str | None = None
    text_to_translate: str | None = None
    translated_text: str | None = None
    is_file_from_gcs: bool = False
