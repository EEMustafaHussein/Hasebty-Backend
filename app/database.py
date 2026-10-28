import os
from collections.abc import Iterator

from dotenv import load_dotenv
from sqlalchemy import Engine, inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401  (importing the models registers the tables)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, echo=False)


# create_all() only creates tables that are missing. A column added later to an existing
# table has to be added here too, or an old database fails with "column does not exist".
NEW_COLUMNS = {"parts": {"image_url": "VARCHAR"}}


def add_missing_columns(bind: Engine) -> None:
    inspector = inspect(bind)
    for table, columns in NEW_COLUMNS.items():
        if not inspector.has_table(table):
            continue
        existing = {column["name"] for column in inspector.get_columns(table)}
        for name, sql_type in columns.items():
            if name not in existing:
                with bind.begin() as connection:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}"))


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
    add_missing_columns(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
