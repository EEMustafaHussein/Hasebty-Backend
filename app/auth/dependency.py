from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.auth.security import decode_access_token
from app.database import get_session
from app.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)
) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token") from None
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_role(role: UserRole):
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=403, detail="You do not have permission to perform this action"
            )
        return current_user

    return role_dependency
