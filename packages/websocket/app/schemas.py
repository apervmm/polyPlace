from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class Pixel(BaseModel):
    x: int
    y: int
    color: str
    timestamp: datetime
    userid: UUID | None = None


class InitMessage(BaseModel):
    type: Literal["init"] = "init"
    pixels: list[Pixel]
    userId: UUID | None = None


class PlaceRequest(BaseModel):
    type: Literal["place"]
    x: int
    y: int
    color: str


class UpdateMessage(BaseModel):
    type: Literal["update"] = "update"
    x: int
    y: int
    color: str
    userId: UUID | None = None
    timestamp: datetime


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    code: Literal["unauthenticated", "rate_limited"]
    message: str
    retryAfterSeconds: float | None = None
