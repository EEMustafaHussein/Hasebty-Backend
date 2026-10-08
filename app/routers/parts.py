from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.auth.dependency import require_role
from app.database import get_session
from app.models import Category, Part, User, UserRole
from app.schemas.part import PartCreate, PartPublic

router = APIRouter(prefix="/parts", tags=["Parts"])


def to_public(part: Part) -> PartPublic:
    return PartPublic(
        id=part.id,
        category_id=part.category_id,
        name=part.name,
        price=part.price,
        stock=part.stock,
        socket=part.socket,
        ram_type=part.ram_type,
        form_factor=part.form_factor,
        wattage=part.wattage,
        specs=part.specs,
    )


@router.get("")
def get_parts(
    category: str | None = None,
    session: Session = Depends(get_session),
):
    query = select(Part).order_by(Part.id)

    if category:
        category_obj = session.exec(
            select(Category).where(Category.name.ilike(category))
        ).first()
        if category_obj is None:
            return {
                "success": True,
                "data": [],
                "message": "Parts retrieved successfully",
            }
        query = query.where(Part.category_id == category_obj.id)

    parts = session.exec(query).all()

    return {
        "success": True,
        "data": [to_public(part) for part in parts],
        "message": "Parts retrieved successfully",
    }


@router.get("/{part_id}")
def get_part(part_id: int, session: Session = Depends(get_session)):
    part = session.get(Part, part_id)
    if part is None:
        raise HTTPException(status_code=404, detail="Part not found")

    return {
        "success": True,
        "data": to_public(part),
        "message": "Part retrieved successfully",
    }


@router.post("", status_code=201)
def create_part(
    data: PartCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_role(UserRole.STAFF)),
):
    if session.get(Category, data.category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found")

    part = Part(**data.model_dump())
    session.add(part)
    session.commit()
    session.refresh(part)

    return {
        "success": True,
        "data": to_public(part),
        "message": "Part created successfully",
    }


@router.put("/{part_id}")
def update_part(
    part_id: int,
    data: PartCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_role(UserRole.STAFF)),
):
    part = session.get(Part, part_id)
    if part is None:
        raise HTTPException(status_code=404, detail="Part not found")

    if session.get(Category, data.category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found")

    for key, value in data.model_dump().items():
        setattr(part, key, value)

    session.add(part)
    session.commit()
    session.refresh(part)

    return {
        "success": True,
        "data": to_public(part),
        "message": "Part updated successfully",
    }
