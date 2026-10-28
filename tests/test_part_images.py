from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, select

import seed
from app.database import add_missing_columns
from app.models import Category, Part
from app.services.part_service import image_link

IMAGE = "https://example.com/images/ryzen-7-5700x.jpg"
APP_DIR = Path(__file__).resolve().parents[1] / "app"


def cpu_category_id(session: Session) -> int:
    return session.exec(select(Category).where(Category.name == "CPU")).one().id or 0


def test_staff_can_add_a_part_with_an_image(
    client: TestClient, session: Session, staff: dict[str, str]
) -> None:
    body = {
        "category_id": cpu_category_id(session),
        "name": "Ryzen 7 5700X",
        "price": 200,
        "stock": 5,
        "image_url": IMAGE,
    }

    response = client.post("/parts", json=body, headers=staff)

    assert response.status_code == 201
    part_id = response.json()["data"]["id"]
    assert client.get(f"/parts/{part_id}").json()["data"]["image_url"] == IMAGE


def test_staff_can_change_the_image(
    client: TestClient, session: Session, staff: dict[str, str]
) -> None:
    part = session.exec(select(Part).where(Part.name == "Ryzen 5 5600")).one()
    body = {
        "category_id": part.category_id,
        "name": part.name,
        "price": part.price,
        "stock": part.stock,
        "image_url": IMAGE,
    }

    assert client.put(f"/parts/{part.id}", json=body, headers=staff).status_code == 200
    assert client.get(f"/parts/{part.id}").json()["data"]["image_url"] == IMAGE


def test_image_is_optional(client: TestClient) -> None:
    parts = client.get("/parts").json()["data"]

    assert all("image_url" in part for part in parts)
    assert parts[0]["image_url"] is None


def test_image_must_be_a_web_link_or_our_picture(
    client: TestClient, session: Session, staff: dict[str, str]
) -> None:
    body = {
        "category_id": cpu_category_id(session),
        "name": "Bad image",
        "price": 1,
        "stock": 1,
        "image_url": "ryzen.jpg",
    }

    response = client.post("/parts", json=body, headers=staff)

    assert response.status_code == 422
    assert "image_url" in response.json()["errors"]


def test_staff_can_use_a_picture_from_our_server(
    client: TestClient, session: Session, staff: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://api.example.com")
    body = {
        "category_id": cpu_category_id(session),
        "name": "Ryzen 7 5700X",
        "price": 200,
        "stock": 5,
        "image_url": "/static/parts/cpu.png",
    }

    response = client.post("/parts", json=body, headers=staff)

    assert response.status_code == 201
    assert response.json()["data"]["image_url"] == "https://api.example.com/static/parts/cpu.png"


def test_category_pictures_are_served(client: TestClient) -> None:
    response = client.get("/static/parts/cpu.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_a_picture_path_becomes_a_full_link(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://api.example.com/")

    assert image_link("/static/parts/cpu.png") == "https://api.example.com/static/parts/cpu.png"
    assert image_link(IMAGE) == IMAGE
    assert image_link(None) is None


def test_seed_gives_every_part_its_category_picture(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    monkeypatch.setattr(seed, "engine", engine)
    monkeypatch.setattr(seed, "create_db_and_tables", lambda: None)

    seed.seed_database()

    with Session(engine) as session:
        parts = session.exec(select(Part)).all()
    assert len(parts) == 50
    for part in parts:
        assert part.image_url is not None
        assert part.image_url.startswith("/static/parts/")
        assert (APP_DIR / part.image_url.lstrip("/")).is_file()


def test_an_old_database_gets_the_new_column() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE parts (id INTEGER PRIMARY KEY, name VARCHAR)"))

    add_missing_columns(engine)

    assert "image_url" in {column["name"] for column in inspect(engine).get_columns("parts")}
