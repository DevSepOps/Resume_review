'''In case of need Token Authentication'''

from fastapi import Depends, HTTPException, status

from fastapi.security import (
    HTTPBasicCredentials,
    HTTPBearer,
)

from users.models import TokenModel,UsersModel

from core.database import get_db

from sqlalchemy.orm import Session


security = HTTPBearer(scheme_name="Token")


def get_authenticated_user(
    credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)
):
    token_obj = (
        db.query(TokenModel).filter_by(token=credentials.credentials).one_or_none()
    )
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Faild to authenticate",
        )
    # other logics for time and etc.
    return token_obj.user
