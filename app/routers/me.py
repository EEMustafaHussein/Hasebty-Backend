from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth.dependency import require_role
from app.database import get_session
from app.models import Build, Order, User, UserRole
from app.routers.build import public_build
from app.schemas.order import OrderPublic

router = APIRouter(prefix="/me", tags=["Customer"])


@router.get("/builds")
def get_my_builds(
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
):
    builds = session.exec(
        select(Build)
        .where(Build.customer_id == current_user.id)
        .order_by(Build.id.desc())
    ).all()

    return {
        "success": True,
        "data": [public_build(session, build) for build in builds],
        "message": "Builds retrieved successfully",
    }


@router.get("/orders")
def get_my_orders(
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
):
    orders = session.exec(
        select(Order)
        .where(Order.customer_id == current_user.id)
        .order_by(Order.id.desc())
    ).all()

    return {
        "success": True,
        "data": [
            OrderPublic(
                id=o.id,
                build_id=o.build_id,
                customer_id=o.customer_id,
                total_price=o.total_price,
                status=o.status,
            )
            for o in orders
        ],
        "message": "Orders retrieved successfully",
    }
