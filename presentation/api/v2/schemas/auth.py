"""Authentication schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    user: Optional[dict] = None


class TokenResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    expires_in: int


class APIKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    expires_days: int = Field(default=365, ge=1, le=3650)


class APIKeyResponse(BaseModel):
    api_key: str
    name: str
    expires_at: str


class APIKeyValidation(BaseModel):
    api_key: str


class LicenseValidateRequest(BaseModel):
    license_key: str = Field(..., min_length=1)
