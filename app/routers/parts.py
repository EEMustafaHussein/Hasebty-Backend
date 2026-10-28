from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session

from app.auth.dependency import require_role
from app.database import get_session
from app.models import Category, Part, User, UserRole
from app.responses import PageParams, page_params, paginated, success
from app.schemas.part import PartCreate
from app.services.image_service import delete_uploaded_image, save_part_image
from app.services.part_service import list_parts, part_to_public

router = APIRouter(prefix="/parts", tags=["Parts"])


@router.get("")
def get_parts(
    category: str | None = None,
    search: str | None = None,
    in_stock: bool | None = None,
    params: PageParams = Depends(page_params),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """List parts. `category` can be a category name (CPU) or id. Paginated with page/limit."""
    parts, total = list_parts(session, params, category, search, in_stock)
    return paginated(
        [part_to_public(p) for p in parts], total, params, "Parts retrieved successfully"
    )


@router.get("/{part_id}")
def get_part(part_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    part = session.get(Part, part_id)
    if part is None:
        raise HTTPException(status_code=404, detail="Part not found")

    return success(part_to_public(part), "Part retrieved successfully")


@router.post("", status_code=201)
def create_part(
    data: PartCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_role(UserRole.STAFF)),
) -> dict[str, Any]:
    if session.get(Category, data.category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found")

    part = Part(**data.model_dump())
    session.add(part)
    session.commit()
    session.refresh(part)

    return success(part_to_public(part), "Part created successfully")


@router.put("/{part_id}")
def update_part(
    part_id: int,
    data: PartCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_role(UserRole.STAFF)),
) -> dict[str, Any]:
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

    return success(part_to_public(part), "Part updated successfully")


@router.post("/{part_id}/image")
def upload_part_image(
    part_id: int,
    file: UploadFile,
    session: Session = Depends(get_session),
    _: User = Depends(require_role(UserRole.STAFF)),
) -> dict[str, Any]:
    """Staff upload a picture for one part from the dashboard (multipart form, field `file`)."""
    part = session.get(Part, part_id)
    if part is None:
        raise HTTPException(status_code=404, detail="Part not found")

    old_image = part.image_url
    part.image_url = save_part_image(part_id, file)
    session.add(part)
    session.commit()
    session.refresh(part)
    delete_uploaded_image(old_image)

    return success(part_to_public(part), "Part image uploaded successfully")
