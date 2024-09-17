from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ProductBase(BaseModel):
    name: str = Field(..., max_length=100, description="The name of the product")
    description: str = Field(..., max_length=500, description="The description of the product")
    price: float = Field(..., gt=0, description="The price of the product")
    category_id: int = Field(..., gt=0, description="The ID of the category to which the product belongs")


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int = Field(..., description="The unique identifier of the product")
    created_at: Optional[datetime] = Field(None, description="The timestamp when the product was created")
    updated_at: Optional[datetime] = Field(None, description="The timestamp when the product was last updated")

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100, description="The name of the category")


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int = Field(..., description="The unique identifier of the category")
    created_at: Optional[datetime] = Field(None, description="The timestamp when the category was created")
    updated_at: Optional[datetime] = Field(None, description="The timestamp when the category was last updated")

    class Config:
        from_attributes = True
