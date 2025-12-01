from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    delivery_address: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    delivery_address: Optional[str] = None
