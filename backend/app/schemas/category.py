from pydantic import BaseModel, Field
from typing import Optional


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    parent_id: Optional[str] = None
    image_url: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    parent_id: Optional[str] = None
    image_url: Optional[str] = None


class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    parent_id: Optional[str]
    image_url: Optional[str]

    model_config = {"from_attributes": True}


class CategoryListResponse(BaseModel):
    categories: list[CategoryResponse]
    total: int
