from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import Session, col, select

from app.auth.dependency import require_role
from app.database import get_session
from app.models import Build, Order, User, UserRole
from app.responses import PageParams, page_params, paginated
from app.services.build_service import build_to_public
from app.services.order_service import order_to_public

router = APIRouter(prefix="/me", tags=["Customer"])


@router.get("/builds")
def get_my_builds(
    params: PageParams = Depends(page_params),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    where = Build.customer_id == current_user.id
    total = session.exec(select(func.count()).select_from(Build).where(where)).one()
    builds = session.exec(
        select(Build)
        .where(where)
        .order_by(col(Build.id).desc())
        .offset(params.offset)
        .limit(params.limit)
    ).all()

    return paginated(
        [build_to_public(session, build) for build in builds],
        total,
        params,
        "Builds retrieved successfully",
    )


@router.get("/orders")
def get_my_orders(
    params: PageParams = Depends(page_params),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    where = Order.customer_id == current_user.id
    total = session.exec(select(func.count()).select_from(Order).where(where)).one()
    orders = session.exec(
        select(Order)
        .where(where)
        .order_by(col(Order.id).desc())
        .offset(params.offset)
        .limit(params.limit)
    ).all()

    return paginated(
        [order_to_public(order) for order in orders],
        total,
        params,
        "Orders retrieved successfully",
    )
