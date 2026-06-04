from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class GuestCreate(BaseModel):  # Post
    name: str = Field(min_length=1)
    email: EmailStr
    room_number: Optional[int] = Field(gt=0, default=None)


class GuestUpdate(BaseModel):  # PATCH
    name: Optional[str] = Field(min_length=1, default=None)
    email: Optional[EmailStr] = None
    room_number: Optional[int] = Field(gt=0, default=None)
    checked_in: Optional[bool] = None


class GuestResponse(BaseModel):  # GET
    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    email: EmailStr
    room_number: Optional[int] = Field(gt=0, default=None)
    checked_in: bool = False


class RoomCreate(BaseModel):
    number: int = Field(gt=0)
    floor: int = Field(ge=1, le=20)
    capacity: int = Field(ge=1, le=6)


class RoomResponse(BaseModel):
    id: int = Field(gt=0)
    number: int = Field(gt=0)
    floor: int = Field(ge=1, le=20)
    capacity: int = Field(ge=1, le=6)
    occupied: bool = False
