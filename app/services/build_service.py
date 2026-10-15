from fastapi import HTTPException
from sqlmodel import Session, col, select

from app.models import Build, BuildPart, Part, User
from app.schemas.build import BuildPublic
from app.services.part_service import part_to_public
from app.utils import require_id


def get_build_parts(session: Session, build_id: int) -> list[Part]:
    statement = (
        select(Part)
        .join(BuildPart, col(Part.id) == col(BuildPart.part_id))
        .where(BuildPart.build_id == build_id)
        .order_by(col(Part.category_id))
    )

    return list(session.exec(statement).all())


def validate_part_ids(session: Session, part_ids: list[int]) -> list[Part]:
    """Business rule 1: a build has one part per category.

    If the list has two parts of the same category, the later one replaces the earlier one
    (this is the decision written in the README).
    """
    parts_by_category: dict[int, Part] = {}

    for part_id in part_ids:
        part = session.get(Part, part_id)

        if part is None:
            raise HTTPException(status_code=404, detail=f"Part {part_id} not found")

        parts_by_category[part.category_id] = part

    return list(parts_by_category.values())


def calculate_total(parts: list[Part]) -> float:
    """Business rule 7: the total price is always calculated here, never sent by the app."""
    return round(sum(part.price for part in parts), 2)


def get_owned_build(session: Session, build_id: int, user: User) -> Build:
    """A customer can only see their own builds. Someone else's build looks like 404."""
    build = session.get(Build, build_id)
    if build is None or build.customer_id != user.id:
        raise HTTPException(status_code=404, detail="Build not found")
    return build


def create_build(session: Session, user: User, name: str, part_ids: list[int]) -> Build:
    parts = validate_part_ids(session, part_ids)

    build = Build(name=name, customer_id=require_id(user.id))
    session.add(build)
    session.flush()  # gives the build an id without committing yet

    for part in parts:
        session.add(
            BuildPart(
                build_id=require_id(build.id),
                category_id=part.category_id,
                part_id=require_id(part.id),
            )
        )

    session.commit()  # build and its parts are saved together or not at all
    session.refresh(build)
    return build


def update_build(session: Session, build: Build, name: str, part_ids: list[int]) -> Build:
    parts = validate_part_ids(session, part_ids)
    build_id = require_id(build.id)

    build.name = name

    old_rows = session.exec(select(BuildPart).where(BuildPart.build_id == build_id)).all()
    for row in old_rows:
        session.delete(row)
    session.flush()  # the old rows must be gone before inserting the new ones

    for part in parts:
        session.add(
            BuildPart(build_id=build_id, category_id=part.category_id, part_id=require_id(part.id))
        )

    session.add(build)
    session.commit()
    session.refresh(build)
    return build


def build_to_public(session: Session, build: Build) -> BuildPublic:
    parts = get_build_parts(session, require_id(build.id))
    return BuildPublic(
        id=require_id(build.id),
        name=build.name,
        customer_id=build.customer_id,
        created_at=build.created_at,
        part_ids=[require_id(part.id) for part in parts],
        parts=[part_to_public(part) for part in parts],
        total=calculate_total(parts),
    )
