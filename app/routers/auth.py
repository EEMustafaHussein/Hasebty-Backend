from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.database import get_session
from app.models import User, UserRole
from app.schemas.auth import RegisterRequest

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register", status_code=201)
def register(
    user_data: RegisterRequest,
    session: Session = Depends(get_session),
):
  
    existing_user = session.exec(
        select(User).where(User.phone == user_data.phone)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Phone number already registered",
        )

    user = User(
        name=user_data.name,
        phone=user_data.phone,
        password_hash=hash_password(user_data.password),
        role=UserRole.CUSTOMER,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "success": True,
        "data": {
            "id": user.id,
            "name": user.name,
            "phone": user.phone,
            "role": user.role.value,
        },
        "message": "Registration successful",
    }


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
 
    user = session.exec(
        select(User).where(User.phone == form_data.username)
    ).first()

    if user is None or not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone or password",
        )

    token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role.value,
        }
    )

    return {
        "success": True,
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "role": user.role.value,
        },
        "message": "Login successful",
    }