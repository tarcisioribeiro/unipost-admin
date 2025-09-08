"""
Text visualization page for UniPOST application.

This page displays generated texts in a grid layout with filtering
capabilities based on approval status.
"""

import streamlit as st
from typing import List, Dict, Any
import requests
from datetime import datetime

from components.auth_components import AuthStateManager
from config.settings import settings


class TextVisualizationPage:
    """
    Page class for text visualization functionality.

    This page handles the display of generated texts with filtering
    and management capabilities.
    """

    def __init__(self) -> None:
        """Initialize the text visualization page."""
        self.auth_manager = AuthStateManager()

    def render(self) -> None:
        """Render the text visualization page."""
        st.set_page_config(
            page_title="Visualização de Textos - UniPOST",
            page_icon="📚",
            layout="wide"
        )

        # Check authentication
        if not self.auth_manager.require_authentication():
            return

        # Render user info in sidebar
        self.auth_manager.render_user_info()

        # Main page content
        st.markdown("# 📚 Visualização de Textos")
        st.markdown(
            "Gerencie e visualize todos os textos gerados pela aplicação.")
        st.markdown("---")

        # Filters
        self._render_filters()

        # Load and display texts
        self._render_texts()

    def _render_filters(self) -> None:
        """Render filtering options."""
        st.markdown("### 🔍 Filtros")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            status_filter = st.selectbox(
                "📊 Status",
                options=["Todos", "Aprovados", "Pendentes", "Negados"],
                key="status_filter"
            )

        with col2:
            date_filter = st.date_input(
                "📅 Data de Criação",
                value=None,
                key="date_filter"
            )

        with col3:
            search_query = st.text_input(
                "🔎 Buscar por tema",
                placeholder="Digite palavras-chave...",
                key="search_query"
            )

        with col4:
            if st.button("🔄 Atualizar", use_container_width=True):
                # Force refresh of texts
                if "cached_texts" in st.session_state:
                    del st.session_state.cached_texts
                st.rerun()

        # Store filters in session
        st.session_state.current_filters = {
            "status": status_filter,
            "date": date_filter,
            "search": search_query
        }

    def _render_texts(self) -> None:
        """Render the grid of texts."""
        # Load texts
        texts = self._load_texts()

        if not texts:
            st.info("📭 Nenhum texto encontrado com os filtros aplicados.")
            return

        # Apply filters
        filtered_texts = self._apply_filters(texts)

        if not filtered_texts:
            st.info("🔍 Nenhum texto encontrado com os critérios de busca.")
            return

        # Display count
        st.markdown(f"### 📄 {len(filtered_texts)} texto(s) encontrado(s)")

        # Render in grid (5 columns as specified)
        self._render_text_grid(filtered_texts)

    def _load_texts(self) -> List[Dict[str, Any]]:
        """
        Load texts from Django API.

        Returns
        -------
        List[Dict[str, Any]]
            List of text documents
        """
        # Check cache first
        if "cached_texts" in st.session_state:
            return st.session_state.cached_texts

        user_token = self.auth_manager.get_user_token()

        try:
            headers = {"Authorization": f"Bearer {user_token}"}

            with st.spinner("📥 Carregando textos..."):
                response = requests.get(
                    f"{settings.django_api_url}/api/texts/",
                    headers=headers,
                    timeout=10
                )

            if response.status_code == 200:
                texts = response.json().get("results", [])
                st.session_state.cached_texts = texts
                return texts
            else:
                st.error(f"Erro ao carregar textos: {response.status_code}")
                return []

        except requests.RequestException as e:
            st.error(f"Erro de conexão: {str(e)}")
            return []

    def _apply_filters(
            self, texts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply filters to text list.

        Parameters
        ----------
        texts : List[Dict[str, Any]]
            Original list of texts

        Returns
        -------
        List[Dict[str, Any]]
            Filtered list of texts
        """
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
                t for t in filtered_texts
                if t.get("created_at", "").startswith(date_str)
            ]

        # Search filter
        search = filters.get("search", "").strip().lower()
        if search:
            filtered_texts = [
                t for t in filtered_texts
                if search in t.get("topic", "").lower() or
                search in t.get("content", "").lower()
            ]

        return filtered_texts

    def _render_text_grid(self, texts: List[Dict[str, Any]]) -> None:
        """
        Render texts in a grid layout (5 columns).

        Parameters
        ----------
        texts : List[Dict[str, Any]]
            List of texts to display
        """
        # Group texts in rows of 5
        rows = [texts[i:i + 5] for i in range(0, len(texts), 5)]

        for row in rows:
            cols = st.columns(5)

            for i, text in enumerate(row):
                with cols[i]:
                    self._render_text_card(text)

    def _render_text_card(self, text: Dict[str, Any]) -> None:
        """
        Render an individual text card.

        Parameters
        ----------
        text : Dict[str, Any]
            Text data to display
        """
        # Determine status
        approval_status = text.get("is_approved")
        if approval_status is True:
            status_emoji = "✅"
            status_text = "Aprovado"
            status_color = "#28a745"
        elif approval_status is False:
            status_emoji = "❌"
            status_text = "Negado"
            status_color = "#dc3545"
        else:
            status_emoji = "⏳"
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

        # Truncate content for card display
        content = text.get("content", "")[:200]
        if len(text.get("content", "")) > 200:
            content += "..."

        topic = text.get("topic", "Sem tema")[:50]
        if len(text.get("topic", "")) > 50:
            topic += "..."

        # Render card
        card_html = f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            height: 300px;
            overflow: hidden;
        ">
            <div style="
                background-color: {status_color};
                color: white;
                padding: 5px 10px;
                border-radius: 15px;
                font-size: 12px;
                display: inline-block;
                margin-bottom: 10px;
            ">
                {status_emoji} {status_text}
            </div>

            <h4 style="
                margin: 10px 0;
                color: #333;
                font-size: 14px;
                font-weight: bold;
            ">
                🎯 {topic}
            </h4>

            <p style="
                color: #666;
                font-size: 12px;
                line-height: 1.4;
                margin: 10px 0;
                height: 120px;
                overflow-y: auto;
            ">
                {content}
            </p>

            <div style="
                margin-top: 10px;
                font-size: 11px;
                color: #999;
                border-top: 1px solid #eee;
                padding-top: 10px;
            ">
                📅 {formatted_date}
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

        # Action buttons for pending texts
        if approval_status is None:
            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "✅",
                    key=f"approve_{text.get('id')}",
                    help="Aprovar",
                    use_container_width=True
                ):
                    self._update_text_status(text.get("id"), True)

            with col2:
                if st.button(
                    "❌",
                    key=f"reject_{text.get('id')}",
                    help="Negar",
                    use_container_width=True
                ):
                    self._update_text_status(text.get("id"), False)

    def _update_text_status(self, text_id: str, is_approved: bool) -> None:
        """
        Update text approval status.

        Parameters
        ----------
        text_id : str
            ID of the text to update
        is_approved : bool
            New approval status
        """
        user_token = self.auth_manager.get_user_token()

        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            data = {"is_approved": is_approved}

            with st.spinner("📤 Atualizando status..."):
                response = requests.patch(
                    f"{settings.django_api_url}/api/texts/{text_id}/",
                    json=data,
                    headers=headers,
                    timeout=10
                )

            if response.status_code in [200, 204]:
                action = "aprovado" if is_approved else "negado"
                st.success(f"✅ Texto {action} com sucesso!")

                # Clear cache to force reload
                if "cached_texts" in st.session_state:
                    del st.session_state.cached_texts

                st.rerun()
            else:
                st.error(f"❌ Erro ao atualizar status: {response.status_code}")

        except requests.RequestException as e:
            st.error(f"❌ Erro de conexão: {str(e)}")


# Initialize and render the page
if __name__ == "__main__":
    page = TextVisualizationPage()
    page.render()
