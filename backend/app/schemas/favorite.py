from pydantic import BaseModel


class FavoriteResponse(BaseModel):
    id: str
    product_id: str
    model_config = {"from_attributes": True}


class FavoriteListResponse(BaseModel):
    favorites: list[FavoriteResponse]
    total: int
