"""Text components for UniPOST application."""

import streamlit as st
from typing import Dict, Any


class TextCard:
    """Component for displaying text cards with metadata."""

    @staticmethod
    def display(text_data: Dict[str, Any]) -> None:
        """Display a text card with title, content and metadata."""
        with st.container():
            st.markdown(f"### {text_data.get('title', 'Texto sem título')}")
            st.write(text_data.get('content', ''))

            # Display metadata if available
            if 'metadata' in text_data:
                with st.expander("Metadados"):
                    for key, value in text_data['metadata'].items():
                        st.write(f"**{key}:** {value}")


class TextFilters:
    """Component for filtering texts."""

    @staticmethod
    def display() -> Dict[str, Any]:
        """Display filter controls and return selected filters."""
        st.sidebar.header("Filtros")

        filters = {}

        # Date filter
        col1, col2 = st.sidebar.columns(2)
        with col1:
            filters['date_from'] = st.date_input("De")
        with col2:
            filters['date_to'] = st.date_input("Até")

        # Category filter
        filters['category'] = st.sidebar.selectbox(
            "Categoria",
            options=["Todas", "Notícias", "Artigos", "Posts"],
            index=0
        )

        # Search text
        filters['search_text'] = st.sidebar.text_input("Buscar texto")

        return filters


class TextGenerator:
    """Component for text generation interface with social platform support."""

    # Platform options matching the API
    PLATFORM_OPTIONS = {
        'FCB': '📘 Facebook',
        'INT': '📸 Instagram',
        'TTK': '🎵 TikTok',
        'LKN': '💼 LinkedIn'
    }

    @staticmethod
    def display() -> Dict[str, Any]:
        """Display text generation form and return parameters."""
        st.header("📱 Geração de Posts")

        form_data = {}

        with st.form("text_generation_form"):
            # Platform selection (primary selection)
            col1, col2 = st.columns(2)
            with col1:
                form_data['platform'] = st.selectbox(
                    "🌐 Plataforma",
                    options=list(TextGenerator.PLATFORM_OPTIONS.keys()),
                    format_func=lambda x: TextGenerator.PLATFORM_OPTIONS[x],
                    index=0,
                    help="Selecione a rede social para otimizar o conteúdo"
                )

            with col2:
                form_data['model'] = "gpt-4o-mini"

                # Topic/subject (primary input)
                form_data['topic'] = st.text_input(
                    "📝 Tema/Assunto",
                    placeholder="Ex: 'Benefícios da inteligência artificial "
                    "no trabalho'",
                    help="Descreva o tema principal do seu post"
                )

            # Advanced options in expander
            with st.expander("⚙️ Opções Avançadas", expanded=True):
                # Target audience
                form_data['audience'] = st.selectbox(
                    "👥 Público-alvo",
                    options=[
                        "Geral",
                        "Jovem (18-25)",
                        "Adulto (26-45)",
                        "Profissional",
                        "Acadêmico",
                        "Técnico"],
                    index=0)

                # Tone adjustment
                form_data['tone'] = st.selectbox(
                    "🎭 Tom do conteúdo",
                    options=[
                        "Automático (baseado na plataforma)",
                        "Formal",
                        "Informal",
                        "Conversacional",
                        "Inspirador",
                        "Educativo",
                        "Promocional"],
                    index=0)

                # Content focus
                form_data['content_focus'] = st.multiselect(
                    "🎯 Foco do conteúdo",
                    options=[
                        "Informativo",
                        "Engajamento",
                        "Call to Action",
                        "Storytelling",
                        "Educacional",
                        "Promocional",
                        "Inspiracional"
                    ],
                    default=["Informativo", "Engajamento"]
                )

                # Additional instructions
                form_data['instructions'] = st.text_area(
                    "💡 Instruções específicas",
                    placeholder="Ex: 'Inclua dados estatísticos', 'Mencione "
                    "nossa empresa', 'Use linguagem técnica'",
                    help="Instruções adicionais para personalizar o conteúdo"
                )

            # Platform-specific preview
            TextGenerator._show_platform_guidelines(
                form_data.get('platform', 'FCB'))

            # Submit button
            form_data['submit'] = st.form_submit_button(
                "🚀 Gerar Conteúdo",
                use_container_width=True,
                type="primary"
            )

        return form_data

    @staticmethod
    def _show_platform_guidelines(platform: str) -> None:
        """Show platform-specific guidelines."""
        guidelines = {
            'FCB': {
                'icon': '📘',
                'tips': [
                    "📝 Ideal: 150-300 palavras",
                    "🔗 Inclua links e CTAs claros",
                    "❓ Faça perguntas para engajamento",
                    "📊 Use dados e insights"
                ]
            },
            'INT': {
                'icon': '📸',
                'tips': [
                    "✨ Ideal: 100-200 palavras",
                    "📱 Linguagem visual e jovem",
                    "💬 Use stories como complemento",
                    "#️⃣ 10-15 hashtags estratégicas"
                ]
            },
            'TTK': {
                'icon': '🎵',
                'tips': [
                    "⚡ Ideal: 50-150 palavras",
                    "🔥 Seja viral e energético",
                    "📈 Use trends atuais",
                    "🎯 Gancho nos primeiros 3s"
                ]
            },
            'LKN': {
                'icon': '💼',
                'tips': [
                    "📄 Ideal: 200-400 palavras",
                    "🎓 Tom profissional e educativo",
                    "📊 Inclua insights de mercado",
                    "🤝 Foque em networking"
                ]
            }
        }

        if platform in guidelines:
            guide = guidelines[platform]
            platform_name = TextGenerator.PLATFORM_OPTIONS[platform]
            tips_text = "\n".join([f"• {tip}" for tip in guide['tips']])
            st.info(
                f"**{guide['icon']} Dicas para {platform_name}:**"
                f"\n{tips_text}")

    @staticmethod
    def display_result(result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Display the generated text result with approval workflow.

        Returns
        -------
        Dict[str, Any]
            Dictionary with button actions: {'approve': bool, 'reject': bool,
            'regenerate': bool}
        """
        if not result_data:
            return {}

        generated_text = result_data.get('content', '')
        platform = result_data.get('platform', 'FCB')
        platform_name = result_data.get('platform_name', 'Facebook')
        text_id = result_data.get('text_id')
        is_stored = result_data.get('stored', False)

        if generated_text:
            # Show storage status
            platform_display = TextGenerator.PLATFORM_OPTIONS.get(
                platform, platform_name
            )
            if is_stored and text_id:
                success_msg = (
                    f"✅ Conteúdo gerado e armazenado para "
                    f"{platform_display}! ID: {text_id}")
                st.success(success_msg)
            else:
                warning_msg = (
                    f"⚠️ Conteúdo gerado para {platform_display}, "
                    f"mas não foi armazenado.")
                st.warning(warning_msg)

            # Main content display
            with st.container():
                title = f"### {platform_display} - Conteúdo Gerado"
                st.markdown(title)
                # Content in a nice box
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 20px;
                border-radius: 10px; border-left: 5px solid #1f77b4;">
                {generated_text.replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

                # Metadata section
                metadata_keys = ['model_used', 'tokens_used', 'generated_at']
                if any(key in result_data for key in metadata_keys):
                    with st.expander("ℹ️ Informações da Geração"):
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            if 'model_used' in result_data:
                                st.metric("🤖 Modelo",
                                          result_data['model_used'])
                        with col2:
                            if 'tokens_used' in result_data:
                                st.metric("🔢 Tokens",
                                          result_data['tokens_used'])
                        with col3:
                            if 'context_length' in result_data:
                                context_metric = (
                                    f"{result_data['context_length']} chars")
                                st.metric("📄 Contexto", context_metric)
                        with col4:
                            if text_id:
                                st.metric("🆔 ID", text_id)

                # Action buttons - 3 main actions as requested
                st.markdown("---")
                st.markdown("### 🎯 Ações para este conteúdo:")
                col1, col2, col3 = st.columns(3)
                actions = {}
                with col1:
                    actions['regenerate'] = st.button(
                        "🔄 Gerar Novamente",
                        use_container_width=True,
                        help="Gerar um novo texto com o mesmo tema "
                             "e plataforma"
                    )

                with col2:
                    actions['approve'] = st.button(
                        "✅ Aprovar",
                        use_container_width=True,
                        type="primary",
                        disabled=not (is_stored and text_id),
                        help="Marcar este texto como aprovado "
                             "(is_approved=True)"
                    )

                with col3:
                    actions['reject'] = st.button(
                        "❌ Descartar",
                        use_container_width=True,
                        disabled=not (is_stored and text_id),
                        help="Marcar este texto como descartado "
                        "(is_approved=False)"
                    )
                # Additional copy button
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("📋 Copiar Texto", use_container_width=True):
                        st.code(generated_text, language=None)
                        st.info(
                            "💡 Texto exibido acima para facilitar a cópia!")

                return actions

        return {}
