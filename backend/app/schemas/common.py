from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    message: str = "ok"
    data: T


class ListPayload(BaseModel, Generic[T]):
    items: list[T]
    total: int


class HealthPayload(BaseModel):
    status: str
    timestamp: datetime

