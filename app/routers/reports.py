from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth.dependency import require_role
from app.database import get_session
from app.models import Order, User, UserRole
from app.responses import success

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/stats")
def get_stats(
    _: User = Depends(require_role(UserRole.STAFF)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    orders = session.exec(select(Order)).all()

    return success(
        {
            "orders": len(orders),
            "revenue": round(sum(order.total_price for order in orders), 2),
        },
        "Stats retrieved successfully",
    )
