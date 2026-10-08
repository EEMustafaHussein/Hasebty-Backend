from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import Category
from app.schemas.category import CategoryPublic

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("")
def get_categories(session: Session = Depends(get_session)):
    categories = session.exec(select(Category).order_by(Category.id)).all()

    return {
        "success": True,
        "data": [CategoryPublic(id=c.id, name=c.name) for c in categories],
        "message": "Categories retrieved successfully",
    }
