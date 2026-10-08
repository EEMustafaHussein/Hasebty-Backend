from pydantic import BaseModel
from app.models import OrderStatus
class OrderCreate(BaseModel):
    build_id: int
class OrderPublic(BaseModel):
    id: int
    build_id: int
    customer_id: int
    total_price: float
    status: OrderStatus
class OrderStatusUpdate(BaseModel):
    status: OrderStatus
