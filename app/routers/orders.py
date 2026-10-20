from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.auth.dependency import require_role
from app.database import get_session
from app.models import Order, OrderStatus, User, UserRole
from app.responses import PageParams, page_params, paginated, success
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.services import order_service
from app.services.order_service import order_to_public

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", status_code=201)
def create_order(
    data: OrderCreate,
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    order = order_service.create_order(session, current_user, data.build_id)
    return success(order_to_public(order), "Order created successfully")


@router.get("")
def get_orders(
    status: OrderStatus | None = None,
    params: PageParams = Depends(page_params),
    _: User = Depends(require_role(UserRole.STAFF)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    statement = select(Order)
    count_statement = select(func.count()).select_from(Order)
    if status is not None:
        statement = statement.where(Order.status == status)
        count_statement = count_statement.where(Order.status == status)

    total = session.exec(count_statement).one()
    orders = session.exec(
        statement.order_by(col(Order.id).desc()).offset(params.offset).limit(params.limit)
    ).all()

    return paginated(
        [order_to_public(order) for order in orders],
        total,
        params,
        "Orders retrieved successfully",
    )


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    _: User = Depends(require_role(UserRole.STAFF)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    order = order_service.change_status(session, order_id, data.status)
    return success(order_to_public(order), "Order status updated successfully")
