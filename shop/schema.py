from datetime import datetime
from typing import List
import uuid
from pydantic import BaseModel, Field, ConfigDict


class CartFilterParams(BaseModel):
    limit: int = Field(10, gt=0, le=1000000)
    offset: int = Field(0, ge=0)


class CartItemSchema(BaseModel):
    sku: str = Field(..., min_length=5, max_length=20)
    name: str = Field(..., min_length=5, max_length=250)
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

    class Config:
        model_config = ConfigDict(from_attributes=True)


class CartSchema(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    items: List[CartItemSchema]
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        model_config = ConfigDict(from_attributes=True)

  
class CartCreateSchema(BaseModel):
    items: List[CartItemSchema]


class CartUpdateSchema(BaseModel):    
    items: List[CartItemSchema]


class CartItemSubtractSchema(BaseModel):
    sku: str = Field(..., min_length=5, max_length=20)
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

    class Config:
        model_config = ConfigDict(from_attributes=True)


class CartSubtractSchema(BaseModel):    
    items: List[CartItemSubtractSchema]
