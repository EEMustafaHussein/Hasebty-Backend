from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class OrderStatus(str, Enum):
    RECEIVED = "received"
    ASSEMBLING = "assembling"
    READY = "ready"
    DELIVERED = "delivered"


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id: int | None = Field(default=None, primary_key=True)
    build_id: int = Field(foreign_key="builds.id")
    customer_id: int = Field(foreign_key="users.id", index=True)
    total_price: float
    status: OrderStatus = Field(default=OrderStatus.RECEIVED)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
