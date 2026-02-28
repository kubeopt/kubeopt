"""Common response schemas."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel


class CloudProviderEnum(str, Enum):
    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int = 400


class SuccessResponse(BaseModel):
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int = 1
    per_page: int = 50
