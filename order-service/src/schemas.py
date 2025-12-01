from pydantic import BaseModel
from typing import List, Optional


class OrderItem(BaseModel):
    name: str
    quantity: int
    price: float


class OrderCreate(BaseModel):
    user_id: str
    email: str
    delivery_address: str
    items: List[OrderItem]


class OrderUpdateStatus(BaseModel):
    status: str  # "processing", "shipping", "delivered"


class OrdersUpdateContact(BaseModel):
    user_id: str
    email: Optional[str] = None
    delivery_address: Optional[str] = None
