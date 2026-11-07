from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import TenantAdminCreate


class TenantRegisterRequest(BaseModel):
    tenant_name: str = Field(min_length=1, max_length=255)
    admin: TenantAdminCreate


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
