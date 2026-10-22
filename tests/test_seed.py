import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import seed
from app.models import Category, Part, User, UserRole


@pytest.fixture
def seeded(monkeypatch: pytest.MonkeyPatch) -> Session:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(seed, "engine", engine)
    monkeypatch.setattr(seed, "create_db_and_tables", lambda: None)
    seed.seed_database()
    return Session(engine)


def test_seed_loads_8_categories_and_50_parts(seeded: Session) -> None:
    assert len(seeded.exec(select(Category)).all()) == 8
    assert len(seeded.exec(select(Part)).all()) == 50


def test_seed_is_safe_to_run_twice(seeded: Session) -> None:
    seed.seed_database()

    assert len(seeded.exec(select(Part)).all()) == 50
    assert len(seeded.exec(select(User)).all()) == 2


def test_staff_phone_has_11_digits_like_the_register_rule(seeded: Session) -> None:
    staff = seeded.exec(select(User).where(User.role == UserRole.STAFF)).one()

    assert staff.role == UserRole.STAFF
    assert staff.phone == "07700000000"
    assert len(staff.phone) == 11


def test_old_10_digit_staff_account_is_fixed(seeded: Session) -> None:
    staff = seeded.exec(select(User).where(User.role == UserRole.STAFF)).one()
    staff.phone = seed.OLD_STAFF_PHONE
    seeded.add(staff)
    seeded.commit()

    seed.seed_database()

    staff_users = seeded.exec(select(User).where(User.role == UserRole.STAFF)).all()
    assert [u.phone for u in staff_users] == ["07700000000"]


def test_seeded_staff_can_log_in(seeded: Session, client: TestClient) -> None:

    from app.database import get_session
    from app.main import app

    app.dependency_overrides[get_session] = lambda: seeded
    try:
        response = TestClient(app).post(
            "/auth/login", data={"username": seed.STAFF_PHONE, "password": seed.STAFF_PASSWORD}
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["data"]["role"] == "staff"


def test_seeded_customer_can_log_in_and_save_a_build(seeded: Session) -> None:
    from app.database import get_session
    from app.main import app

    app.dependency_overrides[get_session] = lambda: seeded
    try:
        client = TestClient(app)
        login = client.post(
            "/auth/login",
            data={"username": seed.CUSTOMER_PHONE, "password": seed.CUSTOMER_PASSWORD},
        )
        headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
        build = client.post("/builds", json={"name": "Demo", "part_ids": [1]}, headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert login.json()["data"]["role"] == "customer"
    assert build.status_code == 201
