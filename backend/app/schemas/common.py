from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T


class MessageResponse(BaseModel):
    success: bool = True
    message: str


class TimestampedModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None = None

