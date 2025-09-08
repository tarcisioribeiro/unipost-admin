"""
Main application entry point for UniPOST Streamlit application.

This module serves as the main entry point and handles the navigation
and authentication flow for the UniPOST text generation application.
"""

import streamlit as st
from components.auth_components import AuthStateManager, LoginForm


class UniPostApp:
    """
    Main application class for UniPOST.

    This class handles the main application flow, including authentication,
    navigation, and page rendering.
    """

    def __init__(self) -> None:
        """Initialize the UniPOST application."""
        self.auth_manager = AuthStateManager()
        self.login_form = LoginForm()

    def run(self) -> None:
        """Run the main application."""
        # Configure page
        st.set_page_config(
            page_title="UniPOST - Geração de Textos com IA",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize session
        self.auth_manager.initialize_session()

        # Check authentication
        if not self.auth_manager.is_authenticated():
            self._render_login_page()
        else:
            self._render_main_app()

    def _render_login_page(self) -> None:
        """Render the login page."""
        # Main content area
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            # App header
            st.markdown(
                """
                <div style="text-align: center; margin: 50px 0;">
                    <h1>🚀 UniPOST</h1>
                    <h3>Geração de Textos com Inteligência Artificial</h3>
                    <p style="color: #666; font-size: 16px;">
                        Sistema inteligente para criação de conteúdo
                        baseado em contexto
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Login form
            self.login_form.render()

            # Footer info
            st.markdown("---")
            st.markdown(
                """
                <div style="text-align: center; color: #888; font-size: 14px;">
                    <p>🔒 Acesso restrito a usuários autorizados</p>
                    <p>📧 Entre em contato com o administrador para obter
                       credenciais</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    def _render_main_app(self) -> None:
        """Render the main application interface."""
        # Sidebar navigation
        self._render_sidebar()

        # Main content
        st.markdown("# 🏠 UniPOST - Dashboard")
        st.markdown("Bem-vindo ao sistema de geração de textos com "
                    "inteligência artificial.")
        st.markdown("---")

        # Dashboard content
        self._render_dashboard()

    def _render_sidebar(self) -> None:
        """Render the application sidebar with navigation."""
        with st.sidebar:
            # App logo/title
            st.markdown(
                """
                <div style="text-align: center; padding: 20px 0;">
                    <h2>🚀 UniPOST</h2>
                    <p style="color: #666; font-size: 12px;">
                       Geração de Textos IA</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Navigation menu
            st.markdown("### 📋 Menu de Navegação")

            # Show navigation instructions
            st.markdown(
                """
                <div style="background-color: #f8f9fa; padding: 15px;
                           border-radius: 5px; margin: 10px 0;">
                    <p style="margin: 0; font-size: 14px;">
                        📌 <strong>Como navegar:</strong><br>
                        Use as páginas disponíveis na barra lateral esquerda
                        para acessar as diferentes funcionalidades.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Service status
            self._render_service_status()

            # User info and logout
            self.auth_manager.render_user_info()

    def _render_service_status(self) -> None:
        """Render service connection status."""
        st.markdown("---")
        st.markdown("### 🔧 Status dos Serviços")

        # This would normally check actual service status
        # For now, showing placeholder status
        services = [
            ("🐳 Redis", "🟢 Conectado"),
            ("🔍 Elasticsearch", "🟡 Verificando"),
            ("🌐 API Django", "🟢 Online")
        ]

        for service, status in services:
            st.markdown(f"**{service}:** {status}")

    def _render_dashboard(self) -> None:
        """Render the main dashboard content."""
        # Quick stats (placeholder)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="📄 Textos Gerados",
                value="--",
                help="Total de textos gerados hoje"
            )

        with col2:
            st.metric(
                label="✅ Aprovados",
                value="--",
                help="Textos aprovados hoje"
            )

        with col3:
            st.metric(
                label="⏳ Pendentes",
                value="--",
                help="Textos aguardando aprovação"
            )

        with col4:
            st.metric(
                label="🎯 Taxa de Aprovação",
                value="--",
                help="Percentual de textos aprovados"
            )

        st.markdown("---")

        # Quick actions
        st.markdown("### 🚀 Ações Rápidas")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "🎯 Gerar Novo Texto",
                use_container_width=True,
                type="primary"
            ):
                st.switch_page("pages/01_🎯_Geração_de_Textos.py")

        with col2:
            if st.button(
                "📚 Ver Todos os Textos",
                use_container_width=True
            ):
                st.switch_page("pages/02_📚_Visualização_de_Textos.py")

        with col3:
            if st.button(
                "🔄 Atualizar Dashboard",
                use_container_width=True
            ):
                st.rerun()

        # Recent activity (placeholder)
        st.markdown("---")
        st.markdown("### 📈 Atividade Recente")

        st.info(
            "📊 As estatísticas e atividades recentes serão exibidas aqui "
            "quando a integração com a API Django estiver completa."
        )

        # Tips and help
        with st.expander("💡 Dicas de Uso"):
            st.markdown(
                """
                **Como usar o UniPOST:**

                1. **🎯 Geração de Textos:**
                   - Acesse a página de geração
                   - Digite um tema ou assunto
                   - Selecione o modelo de IA desejado
                   - Clique em "Gerar Texto"

                2. **📚 Visualização:**
                   - Veja todos os textos gerados
                   - Use filtros por status (aprovado, pendente, negado)
                   - Aprove ou rejeite textos diretamente

                3. **🔍 Busca Inteligente:**
                   - O sistema busca automaticamente por contexto relevante
                   - Os resultados são armazenados em cache para melhor
                     performance

                4. **⚡ Performance:**
                   - Redis é usado para cache de resultados
                   - Elasticsearch fornece busca rápida e precisa
                """
            )


# Initialize and run the application
if __name__ == "__main__":
    app = UniPostApp()
    app.run()
