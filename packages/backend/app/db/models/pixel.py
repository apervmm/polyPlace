from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Pixel(Base):
    __tablename__ = "pixels"
    __table_args__ = (UniqueConstraint("x", "y", name="uq_pixel_xy"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    x: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    y: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    color: Mapped[str] = mapped_column(String, nullable=False)
    userid: Mapped[str | None] = mapped_column(
        String, ForeignKey("users.userid"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )