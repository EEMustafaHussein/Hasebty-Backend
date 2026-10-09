from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.auth.dependency import require_role
from app.database import get_session
from app.models import Order, User, UserRole

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/stats")
def get_stats(
    _: User = Depends(require_role(UserRole.STAFF)),
    session: Session = Depends(get_session),
):
    orders = session.exec(select(Order)).all()

    return {
        "success": True,
        "data": {
            "orders": len(orders),
            "revenue": round(sum(order.total_price for order in orders), 2),
        },
        "message": "Stats retrieved successfully",
    }
