from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, delete

from app.auth.dependency import get_current_user, require_role
from app.database import get_session
from app.models import Build, BuildPart, User, UserRole
from app.schemas.build import BuildCheckPublic, BuildCreate, BuildPublic
from app.services.build_service import calculate_total, get_build_parts, validate_part_ids

router = APIRouter(prefix="/builds", tags=["Builds"])


def public_build(session: Session, build: Build) -> BuildPublic:
    parts = get_build_parts(session, build.id)
    return BuildPublic(
        id=build.id,
        name=build.name,
        customer_id=build.customer_id,
        part_ids=[part.id for part in parts],
    )


@router.post("", status_code=201)
def create_build(
    data: BuildCreate,
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
):
    parts = validate_part_ids(session, data.part_ids)

    build = Build(name=data.name, customer_id=current_user.id)
    session.add(build)
    session.commit()
    session.refresh(build)

    for part in parts:
        session.add(
            BuildPart(
                build_id=build.id,
                category_id=part.category_id,
                part_id=part.id,
            )
        )

    session.commit()

    return {
        "success": True,
        "data": public_build(session, build),
        "message": "Build created successfully",
    }


@router.put("/{build_id}")
def update_build(
    build_id: int,
    data: BuildCreate,
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
):
    build = session.get(Build, build_id)
    if build is None or build.customer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Build not found")

    parts = validate_part_ids(session, data.part_ids)

    build.name = data.name
    session.exec(delete(BuildPart).where(BuildPart.build_id == build.id))

    for part in parts:
        session.add(
            BuildPart(
                build_id=build.id,
                category_id=part.category_id,
                part_id=part.id,
            )
        )

    session.add(build)
    session.commit()
    session.refresh(build)

    return {
        "success": True,
        "data": public_build(session, build),
        "message": "Build updated successfully",
    }


@router.get("/{build_id}/check")
def check_build(
    build_id: int,
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
    session: Session = Depends(get_session),
):
    build = session.get(Build, build_id)
    if build is None or build.customer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Build not found")

    parts = get_build_parts(session, build.id)
    total = calculate_total(parts)

    # Compatibility rules are Week 3 work. The Week 1 contract exposes the endpoint.
    warnings: list[str] = []

    return {
        "success": True,
        "data": BuildCheckPublic(
            build_id=build.id,
            warnings=warnings,
            total=total,
        ),
        "message": "Build checked successfully",
    }
