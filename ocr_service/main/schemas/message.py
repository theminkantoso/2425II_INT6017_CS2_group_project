from pydantic import BaseModel


class MessageSchema(BaseModel):
    type: str | None = None
    file_path: str
    image_hash: str
    encoded_text: str | None = None
    text_to_translate: str | None = None
    translated_text: str | None = None
