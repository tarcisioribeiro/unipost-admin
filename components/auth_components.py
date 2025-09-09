"""
Authentication components for Streamlit interface.

This module contains reusable components for user authentication,
including login forms and session state management.
"""

import streamlit as st
from typing import Optional, Dict, Any

from services.auth_service import AuthService


class LoginForm:
    """
    Login form component for user authentication.

    This component renders a login form and handles user authentication
    through the Django API using the AuthService.
    """

    def __init__(self) -> None:
        """Initialize the login form component."""
        self.auth_service = AuthService()

    def render(self) -> bool:
        """
        Render the login form and handle authentication.

        Returns
        -------
        bool
            True if authentication successful, False otherwise
        """

        with st.form("login_form"):

            username = st.text_input(
                "👤 Usuário",
                placeholder="Digite seu nome de usuário"
            )

            password = st.text_input(
                "🔒 Senha",
                type="password",
                placeholder="Digite sua senha"
            )

            col1, col2, col3 = st.columns([1, 1, 1])

            with col2:
                submit_button = st.form_submit_button(
                    "🚀 Entrar",
                    use_container_width=True,
                    type="primary"
                )

            if submit_button:
                return self._handle_authentication(username, password)

        return False

    def _handle_authentication(self, username: str, password: str) -> bool:
        """
        Handle the authentication process.

        Parameters
        ----------
        username : str
            The entered username
        password : str
            The entered password

        Returns
        -------
        bool
            True if authentication successful, False otherwise
        """
        if not username or not password:
            st.error("⚠️ Por favor, preencha todos os campos.")
            return False

        with st.spinner("🔄 Verificando credenciais..."):
            auth_result = self.auth_service.authenticate_user(username,
                                                              password)

        if auth_result:
            # Store authentication data in session
            st.session_state.authenticated = True
            st.session_state.auth_token = auth_result.get("token")
            st.session_state.user_info = auth_result.get("user")

            st.success("✅ Login realizado com sucesso!")
            st.rerun()
            return True
        else:
            st.error("❌ Credenciais inválidas. Tente novamente.")
            return False


class AuthStateManager:
    """
    Manager for authentication state and user session.

    This class handles authentication state, session validation,
    and provides utilities for managing user sessions.
    """

    def __init__(self) -> None:
        """Initialize the authentication state manager."""
        self.auth_service = AuthService()

    def initialize_session(self) -> None:
        """Initialize session state for authentication."""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "auth_token" not in st.session_state:
            st.session_state.auth_token = None
        if "user_info" not in st.session_state:
            st.session_state.user_info = None

    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated and token is valid.

        Returns
        -------
        bool
            True if user is authenticated with valid token
        """
        if not st.session_state.get("authenticated", False):
            return False

        token = st.session_state.get("auth_token")
        if not token:
            return False

        # Validate token
        if not self.auth_service.validate_token(token):
            self.logout()
            return False

        return True

    def logout(self) -> None:
        """Logout user and clear session data."""
        token = st.session_state.get("auth_token")

        if token:
            self.auth_service.logout_user(token)

        # Clear session state
        st.session_state.authenticated = False
        st.session_state.auth_token = None
        st.session_state.user_info = None

        st.rerun()

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current authenticated user information.

        Returns
        -------
        Optional[Dict[str, Any]]
            Current user information or None
        """
        return st.session_state.get("user_info")

    def get_user_token(self) -> Optional[str]:
        """
        Get current user authentication token.

        Returns
        -------
        Optional[str]
            Current JWT token or None
        """
        return st.session_state.get("auth_token")

    def render_user_info(self) -> None:
        """Render current user information in sidebar."""
        user_info = self.get_current_user()

        if user_info:
            with st.sidebar:
                st.markdown("---")
                st.markdown("### 👤 Usuário Conectado")

                username = user_info.get("username", "Usuário")
                email = user_info.get("email", "")

                st.markdown(f"**{username}**")
                if email:
                    st.markdown(f"📧 {email}")

                if st.button("🚪 Sair", use_container_width=True):
                    self.logout()

    def require_authentication(self) -> bool:
        """
        Ensure user is authenticated, redirect to login if not.

        Returns
        -------
        bool
            True if authenticated, False if redirected to login
        """
        self.initialize_session()

        if not self.is_authenticated():
            st.markdown("# 🚫 Acesso Negado")
            st.error("Você precisa fazer login para acessar esta página.")

            # Show login form
            login_form = LoginForm()
            login_form.render()

            return False

        return True
