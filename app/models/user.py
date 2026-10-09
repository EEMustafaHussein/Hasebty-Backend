from enum import Enum
from sqlmodel import Field, SQLModel
class UserRole(str, Enum):
    CUSTOMER = "customer"
    STAFF = "staff"
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    phone: str = Field(unique=True, index=True)
    password_hash: str
    role: UserRole = Field(default=UserRole.CUSTOMER)
