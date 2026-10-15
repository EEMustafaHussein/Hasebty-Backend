from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select

from app.database import get_session
from app.models import Category
from app.responses import success
from app.schemas.category import CategoryPublic
from app.utils import require_id

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("")
def get_categories(session: Session = Depends(get_session)) -> dict[str, Any]:
    categories = session.exec(select(Category).order_by(col(Category.id))).all()

    return success(
        [CategoryPublic(id=require_id(c.id), name=c.name) for c in categories],
        "Categories retrieved successfully",
    )
