"""
Authentication service for Django API integration.

This module provides authentication functionality to interact with
the Django API using JWT tokens.
"""

from typing import Optional, Dict, Any
import requests
import jwt
from datetime import datetime
import streamlit as st

from config.settings import settings


class AuthService:
    """
    Service class for handling authentication with Django API.

    This service manages user authentication, token validation,
    and session management for the Streamlit application.
    """

    def __init__(self) -> None:
        """Initialize the authentication service."""
        self.base_url = settings.django_api_url
        self.session = requests.Session()

    def authenticate_user(self, username: str,
                          password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user credentials against Django API.

        Parameters
        ----------
        username : str
            The username for authentication
        password : str
            The password for authentication

        Returns
        -------
        Optional[Dict[str, Any]]
            Authentication response with token and user data,
            or None if authentication fails
        """
        try:
            auth_data = {
                "username": username,
                "password": password
            }

            response = self.session.post(
                f"{self.base_url}/api/v1/authentication/token/",
                json=auth_data,
                timeout=10
            )

            if response.status_code == 200:
                auth_data = response.json()
                # Convert JWT response format to expected format
                return {
                    "token": auth_data.get("access"),
                    "refresh_token": auth_data.get("refresh"),
                    "user": {"username": username}  # Basic user info
                }
            else:
                st.error(f"Falha na autenticação: {response.status_code}")
                return None

        except requests.RequestException as e:
            st.error(f"Erro de conexão: {str(e)}")
            return None

    def validate_token(self, token: str) -> bool:
        """
        Validate JWT token.

        Parameters
        ----------
        token : str
            The JWT token to validate

        Returns
        -------
        bool
            True if token is valid, False otherwise
        """
        try:
            # Decode token without verification for expiration check
            decoded = jwt.decode(token, options={"verify_signature": False})

            # Check if token is expired
            exp_timestamp = decoded.get('exp')
            if exp_timestamp:
                exp_date = datetime.fromtimestamp(exp_timestamp)
                if exp_date < datetime.now():
                    return False

            # Validate with Django API
            response = self.session.post(
                f"{self.base_url}/api/v1/authentication/token/verify/",
                json={"token": token},
                timeout=5
            )

            return response.status_code == 200

        except (jwt.DecodeError, requests.RequestException):
            return False

    def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from token.

        Parameters
        ----------
        token : str
            The JWT token containing user information

        Returns
        -------
        Optional[Dict[str, Any]]
            User information dictionary or None if invalid
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.get(
                f"{self.base_url}/api/v1/user/permissions/",
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                return response.json()
            return None

        except requests.RequestException:
            return None

    def logout_user(self, token: str) -> bool:
        """
        Logout user by invalidating token.

        Parameters
        ----------
        token : str
            The JWT token to invalidate

        Returns
        -------
        bool
            True if logout successful, False otherwise
        """
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = self.session.post(
                f"{self.base_url}/api/v1/authentication/logout/",
                headers=headers,
                timeout=5
            )

            return response.status_code in [200, 204]

        except requests.RequestException:
            return False

    @staticmethod
    def is_authenticated() -> bool:
        """
        Check if current session is authenticated.

        Returns
        -------
        bool
            True if user is authenticated, False otherwise
        """
        return st.session_state.get("authenticated", False)

    @staticmethod
    def get_current_user() -> Optional[Dict[str, Any]]:
        """
        Get current authenticated user from session.

        Returns
        -------
        Optional[Dict[str, Any]]
            Current user information or None
        """
        return st.session_state.get("user_info")

    @staticmethod
    def get_current_token() -> Optional[str]:
        """
        Get current authentication token from session.

        Returns
        -------
        Optional[str]
            Current JWT token or None
        """
        return st.session_state.get("auth_token")
