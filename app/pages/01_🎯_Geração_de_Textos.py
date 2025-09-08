"""
Text generation page for UniPOST application.

This page allows users to generate new texts by providing a topic,
selecting a model, and managing the generated content.
"""

import streamlit as st

from components.auth_components import AuthStateManager
from services.text_generation_service import TextGenerationService


class TextGenerationPage:
    """
    Page class for text generation functionality.

    This page handles the interface for text generation,
    model selection, and content approval workflow.
    """

    def __init__(self) -> None:
        """Initialize the text generation page."""
        self.auth_manager = AuthStateManager()
        self.text_service = TextGenerationService()

    def render(self) -> None:
        """Render the text generation page."""
        st.set_page_config(
            page_title="Geração de Textos - UniPOST",
            page_icon="🎯",
            layout="wide"
        )

        # Check authentication
        if not self.auth_manager.require_authentication():
            return

        # Render user info in sidebar
        self.auth_manager.render_user_info()

        # Main page content
        st.markdown("# 🎯 Geração de Textos")
        st.markdown("Crie textos personalizados com base em temas e "
                    "contexto relevante.")
        st.markdown("---")

        # Generation form
        self._render_generation_form()

        # Display generated content if available
        if "generated_text" in st.session_state:
            st.markdown("---")
            self._render_generated_content()

    def _render_generation_form(self) -> None:
        """Render the text generation form."""
        st.markdown("### 📝 Configuração da Geração")

        col1, col2 = st.columns([2, 1])

        with col1:
            topic = st.text_area(
                "💡 Tema do Texto",
                height=100,
                placeholder="Digite o tema ou assunto para geração do "
                "texto...",
                help="Descreva o tema sobre o qual você gostaria de "
                     "gerar um texto"
            )

        with col2:
            # Get available models
            models = self.text_service.get_available_models()

            selected_model = st.selectbox(
                "🤖 Modelo de IA",
                options=models,
                help="Selecione o modelo de inteligência artificial para "
                     "geração"
            )

            st.markdown("### ⚙️ Configurações")

            max_words = st.slider(
                "📏 Tamanho Aproximado (palavras)",
                min_value=100,
                max_value=800,
                value=400,
                step=50
            )

            creativity = st.slider(
                "🎨 Criatividade",
                min_value=0.1,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="0.1 = Mais conservador, 1.0 = Mais criativo"
            )

        # Generate button
        col1, col2, col3 = st.columns([1, 1, 1])

        with col2:
            if st.button(
                "🚀 Gerar Texto",
                use_container_width=True,
                type="primary",
                disabled=not topic.strip()
            ):
                self._handle_text_generation(topic, selected_model,
                                             max_words, creativity)

    def _handle_text_generation(
        self,
        topic: str,
        model: str,
        max_words: int,
        creativity: float
    ) -> None:
        """
        Handle the text generation process.

        Parameters
        ----------
        topic : str
            The topic for text generation
        model : str
            Selected AI model
        max_words : int
            Maximum number of words
        creativity : float
            Creativity level (temperature)
        """
        if not topic.strip():
            st.error("⚠️ Por favor, forneça um tema para a geração.")
            return

        with st.spinner("🔄 Gerando texto... Isso pode levar alguns "
                        "segundos."):
            user_token = self.auth_manager.get_user_token()

            # Update generation parameters
            # Rough estimation of tokens from words
            max_tokens = 150 + (max_words * 2)
            # Store original settings for potential use
            _ = {
                "max_tokens": max_tokens,
                "temperature": creativity
            }

            result = self.text_service.generate_text(
                topic=topic,
                model=model,
                user_token=user_token
            )

        if result:
            # Store in session state
            st.session_state.generated_text = result
            st.session_state.generation_topic = topic
            st.session_state.generation_model = model

            st.success("✅ Texto gerado com sucesso!")
            st.rerun()
        else:
            st.error("❌ Falha na geração do texto. Tente novamente.")

    def _render_generated_content(self) -> None:
        """Render the generated text content with action buttons."""
        st.markdown("### 📄 Texto Gerado")

        generated_data = st.session_state.generated_text

        # Display metadata
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "🎯 Tema",
                st.session_state.get("generation_topic", "N/A")
            )

        with col2:
            st.metric(
                "🤖 Modelo",
                st.session_state.get("generation_model", "N/A")
            )

        with col3:
            generation_time = generated_data.get("generated_at", "N/A")
            if generation_time != "N/A":
                generation_time = generation_time.split("T")[0]
            st.metric("📅 Gerado em", generation_time)

        # Display generated text
        generated_text = generated_data.get("generated_text", "")

        st.markdown("#### Conteúdo:")
        with st.container():
            st.markdown(
                f"""
                <div style="
                    background-color: #f8f9fa;
                    border-left: 4px solid #007acc;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 10px 0;
                    font-size: 16px;
                    line-height: 1.6;
                ">
                {generated_text}
                </div>
                """,
                unsafe_allow_html=True
            )

        # Action buttons
        st.markdown("---")
        st.markdown("### 🎛️ Ações do Texto")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("✅ Aprovar", use_container_width=True,
                         type="primary"):
                self._handle_approval(generated_data.get("id"))

        with col2:
            if st.button("❌ Negar", use_container_width=True):
                self._handle_rejection(generated_data.get("id"))

        with col3:
            if st.button("🔄 Gerar Novamente", use_container_width=True):
                self._handle_regeneration()

        with col4:
            if st.button("🗑️ Limpar", use_container_width=True):
                self._clear_generated_content()

    def _handle_approval(self, text_id: str) -> None:
        """Handle text approval."""
        if not text_id:
            st.error("ID do texto não encontrado.")
            return

        user_token = self.auth_manager.get_user_token()

        with st.spinner("📤 Enviando aprovação..."):
            success = self.text_service.approve_text(text_id, user_token)

        if success:
            st.success("✅ Texto aprovado com sucesso!")
            self._clear_generated_content()
            st.rerun()
        else:
            st.error("❌ Erro ao aprovar o texto.")

    def _handle_rejection(self, text_id: str) -> None:
        """Handle text rejection."""
        if not text_id:
            st.error("ID do texto não encontrado.")
            return

        user_token = self.auth_manager.get_user_token()

        with st.spinner("📤 Enviando rejeição..."):
            success = self.text_service.reject_text(text_id, user_token)

        if success:
            st.success("✅ Texto rejeitado.")
            self._clear_generated_content()
            st.rerun()
        else:
            st.error("❌ Erro ao rejeitar o texto.")

    def _handle_regeneration(self) -> None:
        """Handle text regeneration."""
        topic = st.session_state.get("generation_topic")
        model = st.session_state.get("generation_model")

        if topic and model:
            self._handle_text_generation(topic, model, 400, 0.7)
        else:
            st.error("❌ Informações de geração não encontradas.")

    def _clear_generated_content(self) -> None:
        """Clear generated content from session."""
        keys_to_clear = ["generated_text", "generation_topic",
                         "generation_model"]

        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]


# Initialize and render the page
if __name__ == "__main__":
    page = TextGenerationPage()
    page.render()
