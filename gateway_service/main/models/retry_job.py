from sqlalchemy import Text, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel, TimestampMixin, DeleteMark


class RetryJobModel(BaseModel, TimestampMixin, DeleteMark):
    __tablename__ = "retry_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(255), nullable=False)
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    image_hash: Mapped[str] = mapped_column(Text, nullable=True)
    input_text: Mapped[str] = mapped_column(Text, nullable=True)
    text_hash: Mapped[str] = mapped_column(Text, nullable=True)
    translated_text: Mapped[str] = mapped_column(Text, nullable=True)

