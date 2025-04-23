from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel, TimestampMixin, DeleteMark


class TextCacheModel(BaseModel, TimestampMixin, DeleteMark):
    __tablename__ = "text_cache"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text_encode: Mapped[str] = mapped_column(Text)
    pdf_url: Mapped[str] = mapped_column(Text)
