"""Text components for UniPOST application."""

import streamlit as st
from typing import Dict, List, Optional, Any
import pandas as pd


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
    """Component for text generation interface."""

    @staticmethod
    def display() -> Dict[str, Any]:
        """Display text generation form and return parameters."""
        st.header("Geração de Textos")

        form_data = {}

        with st.form("text_generation_form"):
            # Text type selection
            form_data['text_type'] = st.selectbox(
                "Tipo de texto",
                options=[
                    "Post para redes sociais",
                    "Artigo",
                    "Notícia",
                    "Email"],
                index=0)

            # Topic/subject
            form_data['topic'] = st.text_input(
                "Tópico/Assunto",
                placeholder="Digite o assunto do texto a ser gerado"
            )

            # Target audience
            form_data['audience'] = st.selectbox(
                "Público-alvo",
                options=[
                    "Geral",
                    "Acadêmico",
                    "Profissional",
                    "Jovem",
                    "Técnico"],
                index=0)

            # Tone
            form_data['tone'] = st.selectbox(
                "Tom",
                options=[
                    "Formal",
                    "Informal",
                    "Persuasivo",
                    "Informativo",
                    "Criativo"],
                index=0)

            # Length
            form_data['length'] = st.slider(
                "Tamanho (palavras)",
                min_value=50,
                max_value=1000,
                value=200,
                step=50
            )

            # Additional instructions
            form_data['instructions'] = st.text_area(
                "Instruções adicionais",
                placeholder="Instruções específicas para a geração do texto"
            )

            # Submit button
            form_data['submit'] = st.form_submit_button("Gerar Texto")

        return form_data

    @staticmethod
    def display_result(generated_text: str) -> None:
        """Display the generated text result."""
        if generated_text:
            st.success("Texto gerado com sucesso!")

            with st.container():
                st.markdown("### Texto Gerado")
                st.write(generated_text)

                # Copy button
                if st.button("📋 Copiar texto"):
                    st.write("Texto copiado para a área de transferência!")

                # Save button
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Salvar"):
                        st.success("Texto salvo!")

                with col2:
                    if st.button("📤 Exportar"):
                        st.success("Texto exportado!")
