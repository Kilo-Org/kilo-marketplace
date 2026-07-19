from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OrderCreated(BaseModel):
    order_id: str
    customer_id: str
    total_amount: float
    items: list[str]
    created_at: datetime
    shipping_address: Optional[str] = None

class OrderUpdated(BaseModel):
    order_id: str
    status: str
    updated_at: datetime
    notes: Optional[str] = None
