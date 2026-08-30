from datetime import datetime

from pydantic import BaseModel


class PixelOut(BaseModel):
    x: int
    y: int
    color: str

    class Config:
        from_attributes = True


class PlaceMessage(BaseModel):
    """Incoming WS message: {"type": "place", "x": ..., "y": ..., "color": ...}"""
    type: str
    x: int
    y: int
    color: str


class InitEvent(BaseModel):
    type: str = "init"
    pixels: list[PixelOut]
    userId: str | None


class UpdateEvent(BaseModel):
    type: str = "update"
    x: int
    y: int
    color: str
    userId: str | None
    timestamp: datetime