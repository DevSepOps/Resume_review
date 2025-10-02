from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasicCredentials, HTTPBearer
from users.models import UsersModel
from core.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from core.config import settings
import jwt
from auth.token_blacklist import BlacklistedToken  # Import the new model

security = HTTPBearer()

def get_authenticated_user(
    credentials: HTTPBasicCredentials = Depends(security), 
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    
    # 1. Check if token is blacklisted
    blacklisted_token = db.query(BlacklistedToken).filter(
        BlacklistedToken.token == token
    ).first()
    if blacklisted_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please login again."
        )
    
    # 2. Validate JWT token
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = decoded.get("user_id", None)
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, user_id not in the payload",
            )
        
        if decoded.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, token type not valid",
            )
        
        # Check token expiration
        exp_timestamp = decoded.get("exp")
        current_timestamp = datetime.utcnow().timestamp()
        if current_timestamp > exp_timestamp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed, token expired",
            )
        
        # Get user from database
        user_obj = db.query(UsersModel).filter_by(id=user_id).first()
        if not user_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user_obj.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )
            
        return user_obj

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )

# Keep your existing token generation functions...
def generate_access_token(user_id: int, expire_in: int = 60 * 15) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "type": "access",
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=expire_in)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

def generate_refresh_token(user_id: int, expire_in: int = 3600 * 24) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "type": "refresh",
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=expire_in),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

# Add this new function for token blacklisting
def add_token_to_blacklist(token: str, user_id: int, db: Session):
    """Add token to blacklist and also cleanup expired tokens"""
    
    # Decode token to get expiration time
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        expires_at = datetime.fromtimestamp(decoded.get("exp"))
    except:
        expires_at = datetime.utcnow() + timedelta(hours=24)  # Default 24 hours
    
    # Add to blacklist
    blacklisted_token = BlacklistedToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(blacklisted_token)
    
    # Cleanup expired blacklisted tokens
    db.query(BlacklistedToken).filter(
        BlacklistedToken.expires_at < datetime.utcnow()
    ).delete()
    
    db.commit()