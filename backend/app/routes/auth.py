from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional

from app.core.database import get_db
from app.models.schemas import Token, User, UserCreate, GoogleAuthRequest, TokenPayload
from app.models.models import User as UserModel
from app.services.google_auth import GoogleAuthService
from app.utils.auth import create_access_token, get_password_hash, verify_password, decode_access_token
from datetime import datetime, timedelta


router = APIRouter(tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/token")

# Dependency to get current user from token
async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> UserModel:
    """
    Get the current user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Decode the token
    token_data = decode_access_token(token)
    if token_data is None or token_data.sub is None:
        raise credentials_exception
    
    # Fetch user from database
    user_id = int(token_data.sub)
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    
    if user is None:
        raise credentials_exception
    
    # Check if user is active (optional)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    return user


# Standard login with username/password
@router.post("/token", response_model=Token)
async def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Dict[str, str]:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Query for the user
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)  # Make this configurable
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=User)
async def register_user(
    *, db: Session = Depends(get_db), user_in: UserCreate
) -> Any:
    """
    Create new user
    """
    # Check if user already exists
    user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    db_user = UserModel(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password) if user_in.password else None,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


# Google OAuth routes
@router.get("/google/login")
async def login_google():
    """
    Generate Google OAuth login URL
    """
    auth_url = GoogleAuthService.get_authorization_url()
    return {"auth_url": auth_url}


# Add a new GET route for the Google OAuth callback
@router.get("/accounts/google/login/callback/")
async def google_callback_get(
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
) -> RedirectResponse:
    """
    Handle Google OAuth callback via GET request
    This endpoint receives the authorization code from Google and redirects to the frontend
    with the code as a query parameter
    """
    # Construct the frontend URL to redirect to - match the route in App.js
    frontend_url = "http://localhost:3000/auth/google/callback"
    redirect_url = f"{frontend_url}?code={code}"
    
    if state:
        redirect_url += f"&state={state}"
    
    # Redirect to the frontend callback page
    return RedirectResponse(url=redirect_url)


@router.post("/google/callback", response_model=Token)
async def google_callback_post(
    *, db: Session = Depends(get_db), data: GoogleAuthRequest
) -> Dict[str, str]:
    """
    Process Google OAuth callback
    """
    # Exchange authorization code for tokens
    google_token = GoogleAuthService.exchange_code_for_token(
        code=data.code, redirect_uri=data.redirect_uri
    )
    
    # Get user info from Google
    user_info = GoogleAuthService.get_user_info(google_token.access_token)
    
    if not user_info.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user info from Google",
        )
    
    # Find or create user
    user = db.query(UserModel).filter(UserModel.email == user_info["email"]).first()
    
    if not user:
        # Create a new user
        user = UserModel(
            email=user_info["email"],
            full_name=user_info.get("name", ""),
            google_id=user_info.get("id"),
            google_access_token=google_token.access_token,
            google_refresh_token=google_token.refresh_token,
            token_expiry=datetime.utcnow() + timedelta(seconds=google_token.expires_in),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user with new tokens
        user.google_access_token = google_token.access_token
        if google_token.refresh_token:
            user.google_refresh_token = google_token.refresh_token
        user.token_expiry = datetime.utcnow() + timedelta(seconds=google_token.expires_in)
        db.commit()
        db.refresh(user)
    
    # Create access token for our app
    access_token_expires = timedelta(minutes=30)  # Make this configurable
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """
    Get current user
    """
    return current_user