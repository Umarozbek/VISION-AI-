from fastapi import Depends, HTTPException, Query, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

from fastapi.security import OAuth2PasswordBearer

_optional_bearer = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_stream_user(
    header_token: str | None = Depends(_optional_bearer),
    query_token:  str | None = Query(default=None, alias="access_token"),
    db: Session = Depends(get_db),
) -> User:
    token = header_token or query_token
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET,
                             algorithms=[settings.JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user