"""
Main application entry point for UniPost Streamlit application.

This module serves as the main entry point and handles the navigation
and authentication flow for the UniPost text generation application.
"""

import streamlit as st
from components.auth_components import AuthStateManager, LoginForm
from services.text_generation_service import TextGenerationService
from config.settings import settings
from pages import Dashboard, PostGenerator, PostsViewer, Settings


class UniPostApp:
    """
    Main application class for UniPost.

    This class handles the main application flow, including authentication,
    navigation, and page rendering.
    """

    def __init__(self) -> None:
        """Initialize the UniPost application."""
        self.auth_manager = AuthStateManager()
        self.login_form = LoginForm()
        self.text_service = TextGenerationService()
        
        # Initialize page classes
        self.dashboard = Dashboard()
        self.post_generator = PostGenerator(self.text_service, self.auth_manager)
        self.posts_viewer = PostsViewer(self.auth_manager)
        self.settings = Settings()

    def run(self) -> None:
        """Run the main application."""
        # Configure page
        st.set_page_config(
            page_title="UniPost",
            page_icon="📝",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Load custom CSS
        self._load_custom_css()

        # Initialize session
        self.auth_manager.initialize_session()

        # Check authentication
        if not self.auth_manager.is_authenticated():
            self._render_login_page()
        else:
            self._render_main_app()

    def _load_custom_css(self) -> None:
        """Load custom CSS styles."""
        css_file = "static/styles.css"
        
        try:
            with open(css_file, "r", encoding="utf-8") as f:
                css_content = f.read()
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            # Fallback CSS if file not found
            st.markdown("""
            <style>
            :root {
                --primary-blue: #1e3a8a;
                --secondary-blue: #3b82f6;
                --light-blue: #dbeafe;
                --white: #ffffff;
            }
            .stApp {
                background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
            }
            h1, h2, h3 {
                color: var(--primary-blue);
                font-weight: 700;
            }
            </style>
            """, unsafe_allow_html=True)

    def _render_login_page(self) -> None:
        """Render the login page."""
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown(
                """
                <div class="login-container fade-in">
                    <div class="custom-header">
                        <h1>📝 UniPost</h1>
                        <h3>Aplicação de Geração de Posts</h3>
                    </div>
                """,
                unsafe_allow_html=True
            )

            self.login_form.render()

            st.markdown(
                """
                    <div style="text-align: center; color: var(--medium-gray); 
                                font-size: 14px; margin-top: 20px;">
                        <p>🔒 Acesso restrito • Universidade Marketplaces</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    def _render_main_app(self) -> None:
        """Render the main application interface."""
        self._render_sidebar()

        # Get current page from selectbox
        current_page = st.session_state.get('current_page', 'Dashboard')

        if current_page == 'Dashboard':
            self.dashboard.render_page()
        elif current_page == 'Geração de Posts':
            self.post_generator.render_page()
        elif current_page == 'Visualização de Posts':
            self.posts_viewer.render_page()
        elif current_page == 'Configurações':
            self.settings.render_page()

    def _render_sidebar(self) -> None:
        """Render the application sidebar with navigation."""
        with st.sidebar:
            st.markdown("""
                <div class="custom-header" style="margin: -16px -16px 20px -16px; 
                           text-align: center; padding: 24px 16px;">
                    <h1 style="color: white; margin: 0;">📝 UniPost</h1>
                    <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0 0; 
                              font-size: 14px;">Universidade Marketplaces</p>
                </div>
                """, unsafe_allow_html=True)

            # Check for navigation clicks from buttons
            if "nav_clicked" in st.session_state:
                nav_target = st.session_state.nav_clicked
                del st.session_state.nav_clicked
                st.session_state.current_page = nav_target

            # Navigation selectbox
            nav_options = [
                "Dashboard",
                "Geração de Posts",
                "Visualização de Posts",
                "Configurações"
            ]
            current_page = st.selectbox(
                "Navegação",
                nav_options,
                index=nav_options.index(
                    st.session_state.get("current_page", "Dashboard")
                ),
                key="page_selector"
            )

            # Update session state with selectbox value
            st.session_state.current_page = current_page

            self.auth_manager.render_user_info()


# Initialize and run the application
if __name__ == "__main__":
    app = UniPostApp()
    app.run()
