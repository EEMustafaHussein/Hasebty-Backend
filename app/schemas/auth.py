from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1)

    phone: str = Field(
        min_length=11,
        max_length=11,
        pattern=r"^07\d{9}$",
    )

    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    phone: str = Field(
        min_length=11,
        max_length=11,
        pattern=r"^07\d{9}$",
    )

    password: str


class UserPublic(BaseModel):
    id: int
    name: str
    phone: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
