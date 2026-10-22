from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.dependency import require_role
from app.database import get_session
from app.models import User, UserRole
from app.responses import success
from app.schemas.build import BuildCreate
from app.services import build_service
from app.services.build_service import build_to_public

router = APIRouter(prefix="/builds", tags=["Builds"])


@router.post("", status_code=201)
def create_build(
    data: BuildCreate,
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    build = build_service.create_build(session, current_user, data.name, data.part_ids)
    return success(build_to_public(session, build), "Build created successfully")


@router.get("/{build_id}")
def get_build(
    build_id: int,
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    build = build_service.get_owned_build(session, build_id, current_user)
    return success(build_to_public(session, build), "Build retrieved successfully")


@router.put("/{build_id}")
def update_build(
    build_id: int,
    data: BuildCreate,
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    build = build_service.get_owned_build(session, build_id, current_user)
    build = build_service.update_build(session, build, data.name, data.part_ids)
    return success(build_to_public(session, build), "Build updated successfully")


@router.get("/{build_id}/check")
def check_build(
    build_id: int,
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    build = build_service.get_owned_build(session, build_id, current_user)
    return success(build_service.check_build(session, build), "Build checked successfully")
