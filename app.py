"""
Main application entry point for UniPOST Streamlit application.

This module serves as the main entry point and handles the navigation
and authentication flow for the UniPOST text generation application.
"""

import streamlit as st
from components.auth_components import AuthStateManager, LoginForm
from services.text_generation_service import TextGenerationService
from config.settings import settings
import requests
from typing import List, Dict, Any
from datetime import datetime


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
        self.text_service = TextGenerationService()

    def run(self) -> None:
        """Run the main application."""
        # Configure page
        st.set_page_config(
            page_title="UniPOST",
            page_icon="📝",
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
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown(
                """
                <div style="text-align: center; margin: 50px 0;">
                    <h1>📝 UniPOST</h1>
                    <h3>Sistema de Geração de Textos</h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            self.login_form.render()

            st.markdown("---")
            st.markdown(
                """
                <div style="text-align: center; color: #888; font-size: 14px;">
                    <p>Acesso restrito</p>
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
            self._render_dashboard()
        elif current_page == 'Geração de Textos':
            self._render_text_generation()
        elif current_page == 'Visualização de Textos':
            self._render_text_visualization()

    def _render_sidebar(self) -> None:
        """Render the application sidebar with navigation."""
        with st.sidebar:
            st.markdown("""
                <div style="text-align: center; padding: 20px 0;">
                    <h2>📝 UniPOST</h2>
                </div>
                """, unsafe_allow_html=True)

            # Check for navigation clicks from buttons
            if "nav_clicked" in st.session_state:
                nav_target = st.session_state.nav_clicked
                del st.session_state.nav_clicked
                st.session_state.current_page = nav_target

            # Navigation selectbox
            current_page = st.selectbox(
                "Navegação", [
                    "Dashboard", "Geração de Textos", "Visualização de Textos"], index=[
                    "Dashboard", "Geração de Textos", "Visualização de Textos"].index(
                    st.session_state.get(
                        "current_page", "Dashboard")), key="page_selector")

            # Update session state with selectbox value
            st.session_state.current_page = current_page

            st.markdown("---")

            # Service status
            st.markdown("**Status:**")
            services = [
                ("Redis", "🟢"),
                ("API", "🟢")
            ]
            for service, status in services:
                st.markdown(f"{service}: {status}")

            st.markdown("---")
            self.auth_manager.render_user_info()

    def _render_dashboard(self) -> None:
        """Render the main dashboard content."""
        st.markdown("# Dashboard")
        st.markdown("Sistema de geração de textos com IA")
        st.markdown("---")

        # Stats
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Textos Gerados", "--")

        with col2:
            st.metric("Aprovados", "--")

        with col3:
            st.metric("Pendentes", "--")

        st.markdown("---")

        # Quick actions
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Gerar Novo Texto",
                use_container_width=True,
                    type="primary"):
                st.session_state["nav_clicked"] = "Geração de Textos"
                st.rerun()

        with col2:
            if st.button("Ver Textos", use_container_width=True):
                st.session_state["nav_clicked"] = "Visualização de Textos"
                st.rerun()

    def _render_text_generation(self) -> None:
        """Render the text generation page."""
        st.markdown("# Geração de Textos")
        st.markdown("Crie textos personalizados com IA")
        st.markdown("---")

        # Generation form
        col1, col2 = st.columns([2, 1])

        with col1:
            topic = st.text_area(
                "Tema do Texto",
                height=100,
                placeholder="Digite o tema...",
                help="Descreva o tema para geração"
            )

        with col2:
            models = self.text_service.get_available_models()
            selected_model = st.selectbox("Modelo de IA", options=models)

            st.markdown("**Configurações**")
            max_words = st.slider("Tamanho (palavras)", 100, 800, 400, 50)
            creativity = st.slider("Criatividade", 0.1, 1.0, 0.7, 0.1)

        # Generate button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(
                "Gerar Texto",
                use_container_width=True,
                type="primary",
                    disabled=not topic.strip()):
                self._handle_text_generation(
                    topic, selected_model, max_words, creativity)

        # Display generated content
        if "generated_text" in st.session_state:
            st.markdown("---")
            self._render_generated_content()

    def _handle_text_generation(
            self,
            topic: str,
            model: str,
            max_words: int,
            creativity: float) -> None:
        """Handle the text generation process."""
        if not topic.strip():
            st.error("Por favor, forneça um tema.")
            return

        with st.spinner("Gerando texto..."):
            user_token = self.auth_manager.get_user_token()
            if user_token:
                result = self.text_service.generate_text(
                    topic=topic, model=model, user_token=user_token)
            else:
                st.error("Token de usuário não encontrado")
                return

        if result:
            st.session_state.generated_text = result
            st.session_state.generation_topic = topic
            st.session_state.generation_model = model
            st.success("Texto gerado com sucesso!")
            st.rerun()
        else:
            st.error("Falha na geração. Tente novamente.")

    def _render_generated_content(self) -> None:
        """Render the generated text content."""
        st.markdown("### Texto Gerado")

        generated_data = st.session_state.generated_text
        generated_text = generated_data.get("generated_text", "")

        # Display metadata
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tema", st.session_state.get("generation_topic", "N/A"))
        with col2:
            st.metric(
                "Modelo", st.session_state.get(
                    "generation_model", "N/A"))

        # Display text
        st.markdown("**Conteúdo:**")
        st.markdown(f"""
        <div style="background-color: #f8f9fa; border-left: 4px solid #007acc; padding: 20px; border-radius: 5px; margin: 10px 0; font-size: 16px; line-height: 1.6;">
        {generated_text}
        </div>
        """, unsafe_allow_html=True)

        # Action buttons
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("Aprovar", use_container_width=True, type="primary"):
                self._handle_approval(generated_data.get("id"))

        with col2:
            if st.button("Negar", use_container_width=True):
                self._handle_rejection(generated_data.get("id"))

        with col3:
            if st.button("Gerar Novamente", use_container_width=True):
                self._handle_regeneration()

        with col4:
            if st.button("Limpar", use_container_width=True):
                self._clear_generated_content()

    def _handle_approval(self, text_id: str) -> None:
        """Handle text approval."""
        if not text_id:
            st.error("ID do texto não encontrado.")
            return

        user_token = self.auth_manager.get_user_token()
        with st.spinner("Enviando aprovação..."):
            success = self.text_service.approve_text(text_id, user_token)

        if success:
            st.success("Texto aprovado!")
            self._clear_generated_content()
            st.rerun()
        else:
            st.error("Erro ao aprovar.")

    def _handle_rejection(self, text_id: str) -> None:
        """Handle text rejection."""
        if not text_id:
            st.error("ID do texto não encontrado.")
            return

        user_token = self.auth_manager.get_user_token()
        with st.spinner("Enviando rejeição..."):
            success = self.text_service.reject_text(text_id, user_token)

        if success:
            st.success("Texto rejeitado.")
            self._clear_generated_content()
            st.rerun()
        else:
            st.error("Erro ao rejeitar.")

    def _handle_regeneration(self) -> None:
        """Handle text regeneration."""
        topic = st.session_state.get("generation_topic")
        model = st.session_state.get("generation_model")

        if topic and model:
            self._handle_text_generation(topic, model, 400, 0.7)
        else:
            st.error("Informações de geração não encontradas.")

    def _clear_generated_content(self) -> None:
        """Clear generated content from session."""
        keys_to_clear = [
            "generated_text",
            "generation_topic",
            "generation_model"]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]

    def _render_text_visualization(self) -> None:
        """Render the text visualization page."""
        st.markdown("# Visualização de Textos")
        st.markdown("Gerencie todos os textos gerados")
        st.markdown("---")

        # Filters
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            status_filter = st.selectbox(
                "Status", [
                    "Todos", "Aprovados", "Pendentes", "Negados"], key="status_filter")

        with col2:
            date_filter = st.date_input("Data", value=None, key="date_filter")

        with col3:
            search_query = st.text_input(
                "Buscar",
                placeholder="Palavras-chave...",
                key="search_query")

        with col4:
            if st.button("Atualizar", use_container_width=True):
                if "cached_texts" in st.session_state:
                    del st.session_state.cached_texts
                st.rerun()

        # Store filters
        st.session_state.current_filters = {
            "status": status_filter,
            "date": date_filter,
            "search": search_query
        }

        # Load and display texts
        texts = self._load_texts()
        if not texts:
            st.info("Nenhum texto encontrado.")
            return

        filtered_texts = self._apply_filters(texts)
        if not filtered_texts:
            st.info("Nenhum texto encontrado com os filtros aplicados.")
            return

        st.markdown(f"### {len(filtered_texts)} texto(s) encontrado(s)")
        self._render_text_grid(filtered_texts)

    def _load_texts(self) -> List[Dict[str, Any]]:
        """Load texts from Django API."""
        if "cached_texts" in st.session_state:
            return st.session_state.cached_texts

        user_token = self.auth_manager.get_user_token()

        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            with st.spinner("Carregando textos..."):
                response = requests.get(
                    f"{settings.django_api_url}/api/texts/", headers=headers, timeout=10)

            if response.status_code == 200:
                texts = response.json().get("results", [])
                st.session_state.cached_texts = texts
                return texts
            else:
                st.error(f"Erro ao carregar: {response.status_code}")
                return []
        except requests.RequestException as e:
            st.error(f"Erro de conexão: {str(e)}")
            return []

    def _apply_filters(
            self, texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply filters to text list."""
        filters = st.session_state.get("current_filters", {})
        filtered_texts = texts.copy()

        # Status filter
        status = filters.get("status", "Todos")
        if status != "Todos":
            if status == "Aprovados":
                filtered_texts = [
                    t for t in filtered_texts if t.get("is_approved") is True]
            elif status == "Negados":
                filtered_texts = [
                    t for t in filtered_texts if t.get("is_approved") is False]
            elif status == "Pendentes":
                filtered_texts = [
                    t for t in filtered_texts if t.get("is_approved") is None]

        # Date filter
        date = filters.get("date")
        if date:
            date_str = date.strftime("%Y-%m-%d")
            filtered_texts = [
                t for t in filtered_texts if t.get(
                    "created_at", "").startswith(date_str)]

        # Search filter
        search = filters.get("search", "").strip().lower()
        if search:
            filtered_texts = [
                t for t in filtered_texts if search in t.get(
                    "topic", "").lower() or search in t.get(
                    "content", "").lower()]

        return filtered_texts

    def _render_text_grid(self, texts: List[Dict[str, Any]]) -> None:
        """Render texts in a grid layout."""
        rows = [texts[i:i + 3] for i in range(0, len(texts), 3)]

        for row in rows:
            cols = st.columns(3)
            for i, text in enumerate(row):
                with cols[i]:
                    self._render_text_card(text)

    def _render_text_card(self, text: Dict[str, Any]) -> None:
        """Render an individual text card."""
        approval_status = text.get("is_approved")
        if approval_status is True:
            status_text = "Aprovado"
            status_color = "#28a745"
        elif approval_status is False:
            status_text = "Negado"
            status_color = "#dc3545"
        else:
            status_text = "Pendente"
            status_color = "#ffc107"

        # Format date
        created_at = text.get("created_at", "")
        if created_at:
            try:
                date_obj = datetime.fromisoformat(
                    created_at.replace("Z", "+00:00"))
                formatted_date = date_obj.strftime("%d/%m/%Y %H:%M")
            except ValueError:
                formatted_date = created_at
        else:
            formatted_date = "N/A"

        # Truncate content
        content = text.get("content", "")[:200]
        if len(text.get("content", "")) > 200:
            content += "..."

        topic = text.get("topic", "Sem tema")[:50]
        if len(text.get("topic", "")) > 50:
            topic += "..."

        # Render card
        card_html = f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: 300px; overflow: hidden;">
            <div style="background-color: {status_color}; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; display: inline-block; margin-bottom: 10px;">
                {status_text}
            </div>
            <h4 style="margin: 10px 0; color: #333; font-size: 14px; font-weight: bold;">{topic}</h4>
            <p style="color: #666; font-size: 12px; line-height: 1.4; margin: 10px 0; height: 120px; overflow-y: auto;">{content}</p>
            <div style="margin-top: 10px; font-size: 11px; color: #999; border-top: 1px solid #eee; padding-top: 10px;">{formatted_date}</div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

        # Action buttons for pending texts
        if approval_status is None:
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                        "Aprovar",
                        key=f"""approve_{
                            text.get('id')}""",
                        use_container_width=True):
                    text_id = text.get("id")
                    if text_id:
                        self._update_text_status(text_id, True)
            with col2:
                if st.button(
                        "Negar",
                        key=f"""reject_{
                            text.get('id')}""",
                        use_container_width=True):
                    text_id = text.get("id")
                    if text_id:
                        self._update_text_status(text_id, False)

    def _update_text_status(self, text_id: str, is_approved: bool) -> None:
        """Update text approval status."""
        user_token = self.auth_manager.get_user_token()

        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            data = {"is_approved": is_approved}

            with st.spinner("Atualizando status..."):
                response = requests.patch(
                    f"{settings.django_api_url}/api/texts/{text_id}/", json=data, headers=headers, timeout=10)

            if response.status_code in [200, 204]:
                action = "aprovado" if is_approved else "negado"
                st.success(f"Texto {action}!")
                if "cached_texts" in st.session_state:
                    del st.session_state.cached_texts
                st.rerun()
            else:
                st.error(f"Erro ao atualizar: {response.status_code}")
        except requests.RequestException as e:
            st.error(f"Erro de conexão: {str(e)}")


# Initialize and run the application
if __name__ == "__main__":
    app = UniPostApp()
    app.run()
