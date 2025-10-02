from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request
)
from fastapi.responses import JSONResponse
from users.schemas import UserRegisterSchema, UserLoginSchema, UserRefreshTokenSchema
from users.models import UsersModel, UserRole
from sqlalchemy.orm import Session
from core.database import get_db
from typing import List
from auth.jwt_auth import (
    generate_access_token,
    generate_refresh_token,
    decode_refresh_token,
    add_token_to_blacklist,
    get_authenticated_user
)
import secrets

router = APIRouter(tags=["users"], prefix="/users")

# Simple token generation for further use
def generate_token(length=32):
    return secrets.token_hex(length)


@router.post("/register")
async def user_register(request: UserRegisterSchema, db: Session = Depends(get_db)):
    if db.query(UsersModel).filter_by(username=request.username.lower()).first() or \
        db.query(UsersModel).filter_by(email=request.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username or Email already exists"
        )
    
    # Defining user's role
    role = UserRole.CANDIDATE
    if request.role and request.role == "expert":
        role = UserRole.EXPERT
    
    user_obj = UsersModel(
        username=request.username.lower(),
        email=request.email.lower(),
        github=request.github,
        role=role
    )
    user_obj.set_password(request.password)
    db.add(user_obj)
    db.commit()
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"detail": "User registered successfully"}
    )

@router.post("/login")
async def user_login(request: UserLoginSchema, db: Session = Depends(get_db)):
    user_obj = db.query(UsersModel).filter_by(username=request.username.lower()).first()
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
        )
    
    # ✅ Add password verification
    if not user_obj.verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
        )
    
    # ✅ Generate JWT tokens only (no database token storage)
    access_token = generate_access_token(user_obj.id)
    refresh_token = generate_refresh_token(user_obj.id)
    
    return JSONResponse(
        content={
            "detail": "logged in successfully",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "role": user_obj.role.value
        },
        status_code=status.HTTP_202_ACCEPTED
    )
    
@router.post("/logout")
async def logout(
    request: Request,
    current_user: UsersModel = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    """Logout user by blacklisting the current token"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        
        # ✅ اینجا از تابع import شده استفاده میشه
        add_token_to_blacklist(token, current_user.id, db)
        
        return JSONResponse(
            content={"detail": "Successfully logged out"},
            status_code=status.HTTP_200_OK
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid token provided"
        )


# @router.post("/logout-all") # Testing and Dev
# async def logout_all(
#     current_user: UsersModel = Depends(get_authenticated_user),
#     db: Session = Depends(get_db)
# ):
#     """Logout user from all devices by blacklisting all user's tokens"""
#     # In a real scenario, you might want to track tokens per user
#     # For now, we'll blacklist based on user ID in future implementations
    
#     return JSONResponse(
#         content={"detail": "Logged out from all devices"},
#         status_code=status.HTTP_200_OK
#     )

@router.post("/refresh_token")
async def user_refresh_token(
    request: UserRefreshTokenSchema, 
    db: Session = Depends(get_db)
):
    """Refresh access token - automatically blacklists the old refresh token"""
    user_id = decode_refresh_token(request.token)
    
    # Blacklist the used refresh token
    add_token_to_blacklist(request.token, user_id, db)
    
    # Generate new tokens
    new_access_token = generate_access_token(user_id)
    new_refresh_token = generate_refresh_token(user_id)
    
    return JSONResponse(
        content={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }
    )
