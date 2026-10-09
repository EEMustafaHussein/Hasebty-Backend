import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.models import Category, Part


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
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

        cpu = Part(
            category_id=cpu_category.id,
            name="Ryzen 5 5600",
            price=120,
            stock=10,
        )

        gpu = Part(
            category_id=gpu_category.id,
            name="RTX 4060",
            price=300,
            stock=10,
        )

        session.add(cpu)
        session.add(gpu)
        session.commit()

        session.refresh(cpu)
        session.refresh(gpu)

        yield session