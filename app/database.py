import os
from collections.abc import Iterator

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401  (importing the models registers the tables)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
