from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)

class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    image_file: str | None
    image_path: str


class UserPrivate(UserPublic):
    email: EmailStr


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)

class Token(BaseModel):
    access_token: str
    token_type: str


class DocBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class DocUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class DocResponse(DocBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    file_path: str
    file_type: Literal[
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "txt",
        "jpg",
        "jpeg",
        "png",
        "gif",
        "webp",
    ]
    file_size: int = Field(gt=0, le=100 * 1024 * 1024)
    date_created: datetime
    date_updated: datetime
    folder_id: int | None = None
    owner: UserPublic
