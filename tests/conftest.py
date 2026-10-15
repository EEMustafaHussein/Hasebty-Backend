import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from app.auth.security import hash_password  # noqa: E402
from app.database import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Category, Part, User, UserRole  # noqa: E402

CUSTOMER_PHONE = "07711111111"
OTHER_CUSTOMER_PHONE = "07722222222"
STAFF_PHONE = "07700000000"
PASSWORD = "Pass1234"


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        cpu_category = Category(name="CPU")
        gpu_category = Category(name="GPU")

        session.add(cpu_category)
        session.add(gpu_category)
        session.commit()

        session.refresh(cpu_category)
        session.refresh(gpu_category)

        cpu = Part(category_id=cpu_category.id or 0, name="Ryzen 5 5600", price=120, stock=10)
        gpu = Part(category_id=gpu_category.id or 0, name="RTX 4060", price=300, stock=10)

        session.add(cpu)
        session.add(gpu)

        session.add(
            User(
                name="Customer",
                phone=CUSTOMER_PHONE,
                password_hash=hash_password(PASSWORD),
                role=UserRole.CUSTOMER,
            )
        )
        session.add(
            User(
                name="Other",
                phone=OTHER_CUSTOMER_PHONE,
                password_hash=hash_password(PASSWORD),
                role=UserRole.CUSTOMER,
            )
        )
        session.add(
            User(
                name="Staff",
                phone=STAFF_PHONE,
                password_hash=hash_password(PASSWORD),
                role=UserRole.STAFF,
            )
        )
        session.commit()

        yield session


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    def override_get_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


def login(client: TestClient, phone: str) -> dict[str, str]:
    response = client.post("/auth/login", data={"username": phone, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.fixture
def customer(client: TestClient) -> dict[str, str]:
    return login(client, CUSTOMER_PHONE)


@pytest.fixture
def other_customer(client: TestClient) -> dict[str, str]:
    return login(client, OTHER_CUSTOMER_PHONE)


@pytest.fixture
def staff(client: TestClient) -> dict[str, str]:
    return login(client, STAFF_PHONE)
