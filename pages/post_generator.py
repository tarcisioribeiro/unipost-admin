"""
Módulo para geração de posts.

Este módulo contém a classe PostGenerator responsável por gerenciar
a geração de posts para diferentes plataformas de redes sociais.
"""

import streamlit as st
from typing import Dict, Any
from components.text_components import TextGenerator
from services.text_generation_service import TextGenerationService


class PostGenerator:
    """
    Classe responsável pela geração de posts para redes sociais.
    
    Esta classe encapsula a lógica de geração de posts, incluindo
    a interface do usuário e a integração com os serviços de IA.
    """

    def __init__(self, text_service: TextGenerationService, auth_manager):
        """
        Inicializa o gerador de posts.
        
        Args:
            text_service: Serviço de geração de texto
            auth_manager: Gerenciador de autenticação
        """
        self.text_service = text_service
        self.auth_manager = auth_manager

    def render_page(self) -> None:
        """Renderiza a página de geração de posts."""
        form_data = TextGenerator.display()
        if form_data.get('submit') and form_data.get('topic', '').strip():
            self._handle_platform_text_generation(form_data)

        # Display generated content if available and handle button actions
        if "generated_result" in st.session_state:
            st.divider()
            actions = TextGenerator.display_result(
                st.session_state.generated_result
            )

            # Handle button actions
            if actions.get('approve'):
                self._handle_text_approval()
            elif actions.get('reject'):
                self._handle_text_rejection()
            elif actions.get('regenerate'):
                self._handle_text_regeneration()

    def _handle_platform_text_generation(
        self,
        form_data: Dict[str, Any]
    ) -> None:
        """Handle the platform-specific text generation process."""
        topic = form_data.get('topic', '').strip()
        platform = form_data.get('platform', 'FCB')
        model = form_data.get('model', 'gpt-4o-mini')

        if not topic:
            st.error("Por favor, forneça um tema.")
            return

        platform_name = TextGenerator.PLATFORM_OPTIONS.get(platform, platform)
        with st.spinner(f"Gerando conteúdo para {platform_name}..."):
            user_token = self.auth_manager.get_user_token()
            if user_token:
                result = self.text_service.generate_text(
                    topic=topic,
                    platform=platform,
                    model=model,
                    user_token=user_token
                )
            else:
                st.error("Token de usuário não encontrado")
                return

        if result:
            st.session_state.generated_result = result
            st.session_state.generation_topic = topic
            st.session_state.generation_platform = platform
            st.session_state.generation_model = model
            platform_name = TextGenerator.PLATFORM_OPTIONS.get(
                platform, platform
            )
            st.success(f"Conteúdo gerado para {platform_name}!")
            st.rerun()
        else:
            st.error("Falha na geração. Tente novamente.")

    def _handle_text_approval(self) -> None:
        """Handle text approval from the new workflow."""
        result = st.session_state.get("generated_result", {})
        text_id = result.get("text_id")
        if not text_id:
            st.error("ID do texto não encontrado.")
            return
        user_token = self.auth_manager.get_user_token()
        with st.spinner("Aprovando texto..."):
            success = self.text_service.approve_text(text_id, user_token)
        if success:
            st.success("✅ Texto aprovado com sucesso!")
            self._clear_generated_content()
            st.rerun()
        else:
            st.error("❌ Erro ao aprovar o texto.")

    def _handle_text_rejection(self) -> None:
        """Handle text rejection from the new workflow."""
        result = st.session_state.get("generated_result", {})
        text_id = result.get("text_id")

        if not text_id:
            st.error("ID do texto não encontrado.")
            return

        user_token = self.auth_manager.get_user_token()
        with st.spinner("Descartando texto..."):
            success = self.text_service.reject_text(text_id, user_token)

        if success:
            st.success("✅ Texto descartado com sucesso!")
            self._clear_generated_content()
            st.rerun()
        else:
            st.error("❌ Erro ao descartar o texto.")

    def _handle_text_regeneration(self) -> None:
        """Handle text regeneration from the new workflow."""
        topic = st.session_state.get("generation_topic")
        platform = st.session_state.get("generation_platform")
        model = st.session_state.get("generation_model")

        if topic and platform and model:
            form_data = {
                'topic': topic,
                'platform': platform,
                'model': model
            }
            self._handle_platform_text_generation(form_data)
        else:
            st.error("Informações de geração não encontradas.")

    def _clear_generated_content(self) -> None:
        """Clear generated content from session."""
        keys_to_clear = [
            "generated_result",
            "generation_topic",
            "generation_platform",
            "generation_model"
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]