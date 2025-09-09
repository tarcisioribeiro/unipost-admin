"""
Módulo para visualização de posts.

Este módulo contém a classe PostsViewer responsável por exibir
e gerenciar todos os posts gerados pelo sistema.
"""

import streamlit as st
import requests
from typing import List, Dict, Any
from datetime import datetime, date
from datetime import datetime as dt
from config.settings import settings


class PostsViewer:
    """
    Classe responsável pela visualização e gerenciamento de posts.
    
    Esta classe gerencia a exibição de posts com filtros,
    paginação e ações de aprovação/rejeição.
    """

    def __init__(self, auth_manager):
        """
        Inicializa o visualizador de posts.
        
        Args:
            auth_manager: Gerenciador de autenticação
        """
        self.auth_manager = auth_manager

    def render_page(self) -> None:
        """Renderiza a página de visualização de posts."""
        st.header("Visualização de Posts")
        st.markdown("Gerencie todos os textos gerados")
        st.divider()

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            status_filter = st.selectbox(
                "Status", [
                    "Todos",
                    "Aprovados",
                    "Pendentes",
                    "Negados"
                ],
                key="status_filter"
            )

        # Data padrão: primeiro dia do mês atual
        today = date.today()
        first_day_of_month = today.replace(day=1)

        with col2:
            start_date = st.date_input(
                "Data Inicial",
                value=first_day_of_month,
                key="start_date_filter",
                format="DD/MM/YYYY"
            )

        with col3:
            end_date = st.date_input(
                "Data Final",
                value=today,
                key="end_date_filter",
                format="DD/MM/YYYY"
            )

        # Store filters
        st.session_state.current_filters = {
            "status": status_filter,
            "start_date": start_date,
            "end_date": end_date
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
                    f"{settings.django_api_url}/api/v1/texts/",
                    headers=headers,
                    timeout=10
                )

            if response.status_code == 200:
                response_data = response.json()
                # Handle both list and object with "results" key
                if isinstance(response_data, list):
                    texts = response_data
                else:
                    texts = response_data.get("results", [])
                st.session_state.cached_texts = texts
                return texts
            else:
                st.error(f"Erro ao carregar: {response.status_code}")
                return []
        except requests.RequestException as e:
            st.error(f"Erro de conexão: {str(e)}")
            return []

    def _apply_filters(
        self, texts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply filters to text list."""
        filters = st.session_state.get("current_filters", {})
        filtered_texts = texts.copy()

        # Status filter
        status = filters.get("status", "Todos")
        if status != "Todos":
            if status == "Aprovados":
                filtered_texts = [
                    t for t in filtered_texts if t.get("is_approved") is True
                ]
            elif status == "Negados":
                filtered_texts = [
                    t for t in filtered_texts if t.get("is_approved") is False
                ]
            elif status == "Pendentes":
                filtered_texts = [
                    t for t in filtered_texts if t.get("is_approved") is None
                ]

        # Date range filter
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        
        if start_date or end_date:
            if start_date:
                start_date_str = start_date.strftime("%Y-%m-%d")
            if end_date:
                end_date_str = end_date.strftime("%Y-%m-%d")
            
            def is_date_in_range(created_at_str):
                if not created_at_str:
                    return False
                try:
                    # Extract date part from datetime string
                    date_part = created_at_str.split('T')[0] if 'T' in created_at_str else created_at_str[:10]
                    
                    if start_date and date_part < start_date_str:
                        return False
                    if end_date and date_part > end_date_str:
                        return False
                    return True
                except (ValueError, IndexError):
                    return False
            
            filtered_texts = [
                t for t in filtered_texts if is_date_in_range(t.get("created_at", ""))
            ]

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
        text_id = text.get("id")
        expanded_key = f"expanded_{text_id}"
        edit_key = f"edit_{text_id}"
        
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

        # Full content
        full_content = text.get("content", "")
        
        # Truncate content for preview
        content_preview = full_content[:200]
        if len(full_content) > 200:
            content_preview += "..."

        theme = text.get("theme", "Sem tema")[:50]
        if len(text.get("theme", "")) > 50:
            theme += "..."

        # Get platform display name
        platform_names = {
            'FCB': '📘 Facebook',
            'INT': '📷 Instagram',
            'TTK': '🎵 TikTok',
            'LKN': '💼 LinkedIn'
        }
        platform_display = platform_names.get(
            text.get("platform", ""),
            text.get("platform", "Indefinida")
        )

        # Get status class
        status_class = "status-approved" if approval_status is True else \
                      "status-rejected" if approval_status is False else "status-pending"
        
        # Get platform class
        platform_class_map = {
            'FCB': 'platform-facebook',
            'INT': 'platform-instagram', 
            'TTK': 'platform-tiktok',
            'LKN': 'platform-linkedin'
        }
        platform_class = platform_class_map.get(text.get("platform", ""), "platform-facebook")

        # Check if card is expanded and in edit mode
        is_expanded = st.session_state.get(expanded_key, False)
        is_editing = st.session_state.get(edit_key, False)
        
        # Render card header
        card_html = f"""
        <div class="text-card fade-in">
            <div style="display: flex; justify-content: space-between;
            align-items: center; margin-bottom: 12px;">
                <div class="{status_class}">
                    {status_text}
                </div>
                <div class="{platform_class}">
                    {platform_display}
                </div>
            </div>
            <h4 style="margin: 12px 0; color: var(--primary-blue); font-size: 15px;
            font-weight: bold; line-height: 1.3;">{theme}</h4>
        """

        if is_expanded and is_editing:
            # Show editable content
            card_html += f"""
            <div style="margin: 12px 0; font-size: 12px; color: var(--medium-gray);
            border-top: 1px solid var(--light-blue); padding-top: 12px;
            display: flex; align-items: center; gap: 6px;">
            📅 {formatted_date}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Edit content with text_area
            edited_content = st.text_area(
                "Conteúdo:",
                value=full_content,
                height=200,
                key=f"edit_content_{text_id}",
                help="Edite o conteúdo do post"
            )
        else:
            # Show static content
            content_to_show = full_content if is_expanded else content_preview
            card_html += f"""
            <p style="color: var(--dark-gray); font-size: 13px; line-height: 1.5;
            margin: 12px 0; {'min-height: 140px;' if is_expanded else 'height: 140px;'} overflow-y: auto; 
            border-radius: 6px; padding: 8px; background: var(--light-gray);">{content_to_show}</p>
            <div style="margin-top: 12px; font-size: 12px; color: var(--medium-gray);
            border-top: 1px solid var(--light-blue); padding-top: 12px;
            display: flex; align-items: center; gap: 6px;">
            📅 {formatted_date}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

        # Expand/Collapse button
        expand_text = "Recolher" if is_expanded else "Expandir"
        if st.button(expand_text, key=f"expand_{text_id}", use_container_width=True):
            if not is_expanded:
                # Fechar todos os outros cards expandidos e sair do modo de edição
                keys_to_remove = []
                for key in st.session_state.keys():
                    if key.startswith('expanded_') and key != expanded_key:
                        keys_to_remove.append(key)
                    if key.startswith('edit_') and key != edit_key:
                        keys_to_remove.append(key)
                for key in keys_to_remove:
                    del st.session_state[key]
                # Expandir o card atual
                st.session_state[expanded_key] = True
            else:
                # Recolher o card atual e sair do modo de edição
                st.session_state[expanded_key] = False
                if edit_key in st.session_state:
                    del st.session_state[edit_key]
            st.rerun()

        # Action buttons when expanded
        if is_expanded:
            if is_editing:
                # Edit mode buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(
                        "💾 Salvar",
                        key=f"save_{text_id}",
                        use_container_width=True,
                        help="Salvar alterações"
                    ):
                        edited_content = st.session_state.get(f"edit_content_{text_id}", full_content)
                        if self._update_text_content(text_id, edited_content):
                            st.session_state[edit_key] = False
                            st.rerun()
                        
                with col2:
                    if st.button(
                        "❌ Cancelar",
                        key=f"cancel_{text_id}",
                        use_container_width=True,
                        help="Cancelar edição"
                    ):
                        st.session_state[edit_key] = False
                        st.rerun()
            else:
                # Normal mode buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button(
                        "✏️ Editar",
                        key=f"edit_{text_id}",
                        use_container_width=True,
                        help="Editar conteúdo"
                    ):
                        st.session_state[edit_key] = True
                        st.rerun()
                        
                with col2:
                    if st.button(
                        "✅ Aprovar",
                        key=f"approve_{text_id}",
                        use_container_width=True,
                        help="Aprovar conteúdo"
                    ):
                        if text_id:
                            self._update_text_status(text_id, True)
                            
                with col3:
                    if st.button(
                        "❌ Reprovar",
                        key=f"reject_{text_id}",
                        use_container_width=True,
                        help="Reprovar conteúdo"
                    ):
                        if text_id:
                            self._update_text_status(text_id, False)

    def _update_text_content(self, text_id: str, new_content: str) -> bool:
        """Update text content."""
        user_token = self.auth_manager.get_user_token()

        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            data = {"content": new_content}

            with st.spinner("Salvando alterações..."):
                response = requests.patch(
                    f"{settings.django_api_url}/api/v1/texts/{text_id}/",
                    json=data,
                    headers=headers,
                    timeout=10
                )

            if response.status_code in [200, 204]:
                st.toast("💾 Conteúdo salvo com sucesso!", icon="💾")
                if "cached_texts" in st.session_state:
                    del st.session_state.cached_texts
                return True
            else:
                st.toast(f"⚠️ Erro ao salvar: {response.status_code}", icon="⚠️")
                return False
        except requests.RequestException as e:
            st.toast(f"🔌 Erro de conexão: {str(e)}", icon="🔌")
            return False

    def _update_text_status(self, text_id: str, is_approved: bool) -> None:
        """Update text approval status."""
        user_token = self.auth_manager.get_user_token()

        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            data = {"is_approved": is_approved}

            with st.spinner("Atualizando status..."):
                response = requests.patch(
                    f"{settings.django_api_url}/api/v1/texts/{text_id}/",
                    json=data,
                    headers=headers,
                    timeout=10
                )

            if response.status_code in [200, 204]:
                action = "aprovado" if is_approved else "negado"
                emoji = "✅" if is_approved else "❌"
                st.toast(f"{emoji} Texto {action}!", icon=emoji)
                if "cached_texts" in st.session_state:
                    del st.session_state.cached_texts
                st.rerun()
            else:
                st.toast(f"⚠️ Erro ao atualizar: {response.status_code}", icon="⚠️")
        except requests.RequestException as e:
            st.toast(f"🔌 Erro de conexão: {str(e)}", icon="🔌")