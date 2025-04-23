from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel, TimestampMixin, DeleteMark


class TranslationCacheModel(BaseModel, TimestampMixin, DeleteMark):
    __tablename__ = "translation_cache"

    translation_encode: Mapped[str] = mapped_column(String(255), primary_key=True)
    pdf_url: Mapped[str] = mapped_column(Text)
