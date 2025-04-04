from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import json
import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.models.schemas import GoogleToken


class GoogleAuthService:
    """Service for handling Google OAuth authentication"""
    
    @staticmethod
    def get_authorization_url(redirect_uri: str = None) -> str:
        """Generate Google OAuth authorization URL"""
        # Load client secrets from credentials.json
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": settings.GOOGLE_AUTH_URI,
                "token_uri": settings.GOOGLE_TOKEN_URI,
                "redirect_uris": [redirect_uri or settings.GOOGLE_REDIRECT_URI]
            }
        }
        
        # Create flow instance
        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=settings.GOOGLE_SCOPES,
            redirect_uri=redirect_uri or settings.GOOGLE_REDIRECT_URI
        )
        
        # Generate authorization URL
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            include_granted_scopes='true'
        )
        
        return auth_url

    @staticmethod
    def exchange_code_for_token(code: str, redirect_uri: str = None) -> GoogleToken:
        """Exchange authorization code for tokens"""
        # Load client secrets from credentials.json
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": settings.GOOGLE_AUTH_URI,
                "token_uri": settings.GOOGLE_TOKEN_URI,
                "redirect_uris": [redirect_uri or settings.GOOGLE_REDIRECT_URI]
            }
        }
        
        # Create flow instance
        flow = Flow.from_client_config(
            client_config=client_config,
            scopes=settings.GOOGLE_SCOPES,
            redirect_uri=redirect_uri or settings.GOOGLE_REDIRECT_URI
        )
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        
        # Get credentials
        credentials = flow.credentials
        
        # Return tokens
        return GoogleToken(
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            expires_in=credentials.expiry.timestamp() if credentials.expiry else 0,
            token_type=credentials.token_type,
            id_token=credentials.id_token
        )

    @staticmethod
    def get_user_info(access_token: str) -> Dict[str, Any]:
        """Get Google user information using access token"""
        credentials = Credentials(token=access_token)
        service = build('oauth2', 'v2', credentials=credentials)
        
        try:
            user_info = service.userinfo().get().execute()
            return user_info
        except HttpError as error:
            print(f"An error occurred: {error}")
            return {}

    @staticmethod
    def create_credentials(
        access_token: str, 
        refresh_token: Optional[str] = None, 
        expiry: Optional[datetime] = None
    ) -> Credentials:
        """Create Google Credentials object from tokens"""
        return Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=settings.GOOGLE_TOKEN_URI,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=settings.GOOGLE_SCOPES,
            expiry=expiry
        )

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=settings.GOOGLE_TOKEN_URI,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=settings.GOOGLE_SCOPES
        )
        
        # Refresh the credentials
        credentials.refresh(None)
        
        # Return new tokens
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token or refresh_token,
            "expires_in": credentials.expiry.timestamp() if credentials.expiry else 0,
            "token_type": credentials.token_type
        }