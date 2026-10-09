from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.auth.dependency import require_role
from app.database import get_session
from app.models import Build, Order, OrderStatus, User, UserRole
from app.schemas.order import OrderCreate, OrderPublic, OrderStatusUpdate
from app.services.build_service import calculate_total, get_build_parts

router = APIRouter(prefix="/orders", tags=["Orders"])

STATUS_ORDER = {
    OrderStatus.RECEIVED: 0,
    OrderStatus.ASSEMBLING: 1,
    OrderStatus.READY: 2,
    OrderStatus.DELIVERED: 3,
}


def to_public(order: Order) -> OrderPublic:
    return OrderPublic(
        id=order.id,
        build_id=order.build_id,
        customer_id=order.customer_id,
        total_price=order.total_price,
        status=order.status,
    )


@router.post("", status_code=201)
def create_order(
    data: OrderCreate,
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
):
    build = session.get(Build, data.build_id)
    if build is None or build.customer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Build not found")

    parts = get_build_parts(session, build.id)
    if any(part.stock <= 0 for part in parts):
        raise HTTPException(status_code=400, detail="A part with zero stock cannot be ordered")

    total = calculate_total(parts)
    order = Order(
        build_id=build.id,
        customer_id=current_user.id,
        total_price=total,
    )
    session.add(order)
    session.commit()
    session.refresh(order)

    return {
        "success": True,
        "data": to_public(order),
        "message": "Order created successfully",
    }


@router.get("")
def get_orders(
    status: OrderStatus | None = None,
    _: User = Depends(require_role(UserRole.STAFF)),
    session: Session = Depends(get_session),
):
    query = select(Order).order_by(Order.id.desc())
    if status is not None:
        query = query.where(Order.status == status)

    orders = session.exec(query).all()

    return {
        "success": True,
        "data": [to_public(order) for order in orders],
        "message": "Orders retrieved successfully",
    }


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    _: User = Depends(require_role(UserRole.STAFF)),
    session: Session = Depends(get_session),
):
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    if STATUS_ORDER[data.status] < STATUS_ORDER[order.status]:
        raise HTTPException(status_code=400, detail="Order status can only move forward")

    order.status = data.status
    session.add(order)
    session.commit()
    session.refresh(order)

    return {
        "success": True,
        "data": to_public(order),
        "message": "Order status updated successfully",
    }
