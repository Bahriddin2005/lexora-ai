import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=80)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str | None
    role: str
    plan: str
    ui_language: str
    created_at: datetime


class AuthOut(BaseModel):
    user: UserOut
    access_token: str


class UserUpdateIn(BaseModel):
    display_name: str | None = Field(default=None, max_length=80)
    ui_language: str | None = Field(default=None, max_length=8)
