from typing import Literal

from pydantic import BaseModel, Field


class ListingCreate(BaseModel):
    ticker: str = Field(min_length=1)
    price: float = Field(gt=0)
    company: str = Field(min_length=1)


class ListingResponse(BaseModel):
    id: int = Field(gt=0)
    ticker: str
    price: float
    company: str


class ListingCollectionResponse(BaseModel):
    items: list[ListingResponse]


class OrderCreate(BaseModel):
    listing_id: int = Field(gt=0)
    side: Literal["buy", "sell"]
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)


class OrderResponse(BaseModel):
    id: int = Field(gt=0)
    listing_id: int
    side: str
    quantity: int
    price: float


class OrderCollectionResponse(BaseModel):
    items: list[OrderResponse]
