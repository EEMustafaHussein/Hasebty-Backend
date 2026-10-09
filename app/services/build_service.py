from fastapi import HTTPException
from sqlmodel import Session, select
from app.models import BuildPart, Part

def get_build_parts(session: Session, build_id: int) -> list[Part]:
    statement = (
        select(Part)
        .join(BuildPart, Part.id == BuildPart.part_id)
        .where(BuildPart.build_id == build_id)
    )

    return list(session.exec(statement).all())


def validate_part_ids(
    session: Session,
    part_ids: list[int],
) -> list[Part]:
    parts_by_category: dict[int, Part] = {}

    for part_id in part_ids:
        part = session.get(Part, part_id)

        if part is None:
            raise HTTPException(
                status_code=404,
                detail=f"Part {part_id} not found",
            )

    
        parts_by_category[part.category_id] = part

    return list(parts_by_category.values())


def calculate_total(parts: list[Part]) -> float:
    return round(sum(part.price for part in parts), 2)