from sqlmodel import select

from app.models import Part
from app.services.build_service import (
    calculate_total,
    validate_part_ids,
)


def test_validate_part_ids(session):
    parts = session.exec(select(Part)).all()

    result = validate_part_ids(
        session,
        [parts[0].id, parts[1].id],
    )

    assert len(result) == 2


def test_same_category_replaces_old_part(session):
    parts = session.exec(select(Part)).all()

    first = parts[0]

    second = Part(
        category_id=first.category_id,
        name="Ryzen 7 5700X",
        price=200,
        stock=10,
    )

    session.add(second)
    session.commit()
    session.refresh(second)

    result = validate_part_ids(
        session,
        [first.id, second.id],
    )

    assert len(result) == 1
    assert result[0].id == second.id


def test_calculate_total(session):
    parts = session.exec(select(Part)).all()

    assert calculate_total(parts) == 420
