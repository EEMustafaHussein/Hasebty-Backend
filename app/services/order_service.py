from fastapi import HTTPException
from sqlmodel import Session

from app.models import Order, OrderStatus, User
from app.schemas.order import OrderPublic
from app.services.build_service import (
    calculate_total,
    check_build,
    get_build_parts,
    get_owned_build,
)
from app.utils import require_id

STATUS_ORDER = {
    OrderStatus.RECEIVED: 0,
    OrderStatus.ASSEMBLING: 1,
    OrderStatus.READY: 2,
    OrderStatus.DELIVERED: 3,
}


def order_to_public(order: Order) -> OrderPublic:
    return OrderPublic(
        id=require_id(order.id),
        build_id=order.build_id,
        customer_id=order.customer_id,
        total_price=order.total_price,
        status=order.status,
        created_at=order.created_at,
    )


def create_order(session: Session, user: User, build_id: int) -> Order:
    build = get_owned_build(session, build_id, user)
    parts = get_build_parts(session, require_id(build.id))

    if not parts:
        raise HTTPException(status_code=400, detail="An empty build cannot be ordered")

    # Business rule 6: a build with any compatibility problem cannot be ordered.
    if check_build(session, build).warnings:
        raise HTTPException(
            status_code=400, detail="This build has compatibility problems and cannot be ordered"
        )

    # Business rule 8: a part with zero stock cannot be ordered.
    if any(part.stock <= 0 for part in parts):
        raise HTTPException(status_code=400, detail="A part with zero stock cannot be ordered")

    order = Order(
        build_id=require_id(build.id),
        customer_id=require_id(user.id),
        total_price=calculate_total(parts),
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def change_status(session: Session, order_id: int, new_status: OrderStatus) -> Order:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # Business rule 9: the status only moves forward.
    if STATUS_ORDER[new_status] < STATUS_ORDER[order.status]:
        raise HTTPException(status_code=400, detail="Order status can only move forward")

    order.status = new_status
    session.add(order)
    session.commit()
    session.refresh(order)
    return order
