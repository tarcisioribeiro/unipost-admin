import streamlit as st
from typing import List, Dict
import logging
import html

logger = logging.getLogger(__name__)


class SearchResults:
    """
    Classe para exibir resultados de busca dos embeddings via API
    """

    def __init__(self):
        from services.embeddings_service import EmbeddingsService
        self.embeddings_service = EmbeddingsService()

    def display_search_interface(self):
        """
        Interface de busca para o usuário com suporte a metadados
        """
        st.subheader("🔍 Busca na Base de Embeddings")

        # Verificar conexão com a API
        if not self.embeddings_service.health_check():
            st.toast("API de embeddings não está disponível", icon="❌")
            return

        # Abas para diferentes tipos de busca
        tab_text, tab_metadata, tab_advanced = st.tabs([
            "📝 Busca Textual",
            "🏷️ Busca por Metadados",
            "⚙️ Busca Avançada"
        ])

        with tab_text:
            self._display_text_search()

        with tab_metadata:
            self._display_metadata_search()

        with tab_advanced:
            self._display_advanced_search()

    def _display_text_search(self):
        """
        Interface de busca textual tradicional
        """
        st.markdown("### Busca textual simples")

        # Interface de busca
        col_search, col_button = st.columns([3, 1])

        with col_search:
            search_query = st.text_input(
                "Digite sua consulta:",
                placeholder="Ex: marketing digital, vendas, consultoria...",
                help="Busque por temas, estratégias, ou palavras-chave",
                key="search_text_query"
            )

        with col_button:
            search_button = st.button(
                "🔍 Buscar",
                type="primary",
                use_container_width=True,
                help="Buscar nos embeddings",
                key="text_search_btn"
            )

        # Configurações simples
        result_size = st.slider(
            "Número máximo de resultados:",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            help="Quantidade de resultados"
        )

        # Executar busca
        if search_button and search_query.strip():
            self._perform_text_search(search_query.strip(), result_size)
        elif search_button and not search_query.strip():
            st.toast("Por favor, digite uma consulta para buscar.", icon="⚠️")

    def _display_metadata_search(self):
        """
        Interface de busca por metadados específicos
        """
        st.markdown("### Busca por metadados específicos")

        # Informação sobre metadados
        st.info(
            "💡 **Dica:** Use os filtros abaixo para buscar por "
            "características específicas dos embeddings.")

        # Formulário de busca por metadados
        col_meta1, col_meta2 = st.columns(2)

        with col_meta1:
            # Filtros categóricos
            author_filter = st.text_input(
                "👤 Autor:",
                placeholder="Ex: João Silva",
                help="Buscar por autor específico",
                key="metadata_author"
            )

            platform_filter = st.selectbox(
                "📱 Plataforma:",
                options=[
                    "",
                    "Facebook",
                    "Instagram",
                    "LinkedIn",
                    "TikTok",
                    "Twitter",
                    "YouTube"],
                help="Selecionar plataforma específica",
                key="metadata_platform")

            theme_filter = st.text_input(
                "🎯 Tema:",
                placeholder="Ex: marketing",
                help="Buscar por tema específico",
                key="metadata_theme"
            )

        with col_meta2:
            # Filtros adicionais
            tags_filter = st.text_input(
                "🏷️ Tags:",
                placeholder="Ex: social media",
                help="Buscar por tags específicas",
                key="metadata_tags"
            )

            origin_filter = st.selectbox(
                "🗂️ Origem:",
                options=[
                    "",
                    "webscraping",
                    "generated",
                    "business_brain",
                    "manual"],
                help="Filtrar por origem do conteúdo",
                key="metadata_origin")

            content_type_filter = st.selectbox(
                "📄 Tipo de Conteúdo:",
                options=["", "post", "article", "video", "image", "text"],
                help="Filtrar por tipo de conteúdo",
                key="metadata_content_type"
            )

        # Filtros numéricos
        st.markdown("**Filtros Numéricos:**")
        col_num1, col_num2 = st.columns(2)

        with col_num1:
            word_count_min = st.number_input(
                "📊 Palavras mínimas:",
                min_value=0,
                value=0,
                help="Número mínimo de palavras",
                key="metadata_word_min"
            )

        with col_num2:
            word_count_max = st.number_input(
                "📊 Palavras máximas:",
                min_value=0,
                value=1000,
                help="Número máximo de palavras",
                key="metadata_word_max"
            )

        # Botão de busca por metadados
        result_size_meta = st.slider(
            "Resultados:",
            min_value=5,
            max_value=50,
            value=15,
            key="metadata_result_size"
        )

        if st.button(
            "🔍 Buscar por Metadados",
            type="primary",
                key="metadata_search_btn"):
            # Preparar critérios de busca
            search_criteria = {}

            if author_filter:
                search_criteria['author'] = author_filter
            if platform_filter:
                search_criteria['platform'] = platform_filter
            if theme_filter:
                search_criteria['theme'] = theme_filter
            if tags_filter:
                search_criteria['tags'] = tags_filter
            if origin_filter:
                search_criteria['origin'] = origin_filter
            if content_type_filter:
                search_criteria['content_type'] = content_type_filter
            if word_count_min > 0:
                search_criteria['word_count_min'] = str(word_count_min)
            if word_count_max < 1000:
                search_criteria['word_count_max'] = str(word_count_max)

            if search_criteria:
                self._perform_metadata_search(
                    search_criteria, result_size_meta)
            else:
                st.toast("Defina ao menos um critério de busca", icon="⚠️")

    def _display_advanced_search(self):
        """
        Interface de busca avançada combinando texto e metadados
        """
        st.markdown("### Busca avançada (texto + metadados)")

        # Query textual
        search_query = st.text_area(
            "🔍 Consulta textual:",
            placeholder="Digite sua consulta principal...",
            height=100,
            key="advanced_query"
        )

        # Filtros de metadados (versão simplificada)
        col_adv1, col_adv2, col_adv3 = st.columns(3)

        with col_adv1:
            theme = st.text_input("🎯 Tema:", key="adv_theme")
            platform = st.text_input("📱 Plataforma:", key="adv_platform")

        with col_adv2:
            origin = st.text_input("🗂️ Origem:", key="adv_origin")
            author = st.text_input("👤 Autor:", key="adv_author")

        with col_adv3:
            created_after = st.date_input(
                "📅 Após:", key="adv_date_after", value=None)
            created_before = st.date_input(
                "📅 Antes:", key="adv_date_before", value=None)

        # Campos de busca específicos
        search_fields = st.multiselect(
            "🎯 Campos para buscar:",
            options=['title', 'content', 'theme'],
            default=['title', 'content'],
            help="Selecione os campos onde buscar o texto",
            key="adv_search_fields"
        )

        result_size_adv = st.slider(
            "Máximo de resultados:",
            5, 30, 15,
            key="adv_result_size"
        )

        # Botão de busca avançada
        if st.button(
            "🚀 Busca Avançada",
            type="primary",
                key="advanced_search_btn"):
            if search_query.strip() or any([theme, platform, origin, author]):
                self._perform_advanced_search(
                    query=search_query or "",
                    theme=theme or "",
                    platform=platform or "",
                    origin=origin or "",
                    author=author or "",
                    created_after=(created_after.isoformat()
                                   if created_after else ""),
                    created_before=(created_before.isoformat()
                                    if created_before else ""),
                    search_fields=search_fields,
                    size=result_size_adv)
            else:
                st.toast(
                    "Forneça uma consulta textual ou filtros de metadados",
                    icon="⚠️")

    def _perform_text_search(self, query: str, size: int):
        """
        Executa busca textual simples
        """
        with st.spinner(f"🔍 Buscando por '{query}'..."):
            try:
                results = self.embeddings_service.query_embeddings_by_text(
                    query)
                if len(results) > size:
                    results = results[:size]

                if not results:
                    st.toast("Nenhum resultado encontrado.", icon="📭")
                    self._display_search_tips()
                    return

                self._display_search_statistics(results, query)
                self._display_search_results(results, show_metadata=True)

            except Exception as e:
                logger.error(f"Error during text search: {e}")
                st.toast("Erro durante a busca textual", icon="❌")

    def _perform_metadata_search(self, search_criteria: dict, size: int):
        """
        Executa busca baseada em metadados específicos
        """
        with st.spinner("🏷️ Buscando por metadados..."):
            try:
                # Usar busca por texto para simular busca por metadados
                search_terms = []
                for key, value in search_criteria.items():
                    if value:
                        search_terms.append(value)

                if search_terms:
                    query = " ".join(search_terms)
                    results = self.embeddings_service.query_embeddings_by_text(
                        query)
                    if len(results) > size:
                        results = results[:size]
                else:
                    results = []

                if not results:
                    st.toast(
                        "Nenhum resultado encontrado com os critérios.",
                        icon="📭"
                    )
                    st.info(
                        "Tente ajustar os filtros ou usar critérios "
                        "mais amplos."
                    )
                    return

                # Exibir critérios usados
                criteria_display = []
                for key, value in search_criteria.items():
                    if value:
                        criteria_display.append(f"{key}: {value}")

                st.success(
                    f"**Critérios aplicados:** {', '.join(criteria_display)}"
                )

                self._display_search_statistics(results, "metadados")
                self._display_search_results(results, show_metadata=True)

            except Exception as e:
                logger.error(f"Error during metadata search: {e}")
                st.toast("Erro durante a busca por metadados", icon="❌")

    def _perform_advanced_search(
        self, query: str, theme: str, platform: str, origin: str,
        author: str, created_after: str, created_before: str,
        search_fields: list, size: int
    ):
        """
        Executa busca avançada combinando texto e metadados
        """
        with st.spinner("🚀 Executando busca avançada..."):
            try:
                # Combinar todos os termos para busca avançada
                search_terms = []
                if query.strip():
                    search_terms.append(query)
                if theme:
                    search_terms.append(theme)
                if platform:
                    search_terms.append(platform)
                if origin:
                    search_terms.append(origin)
                if author:
                    search_terms.append(author)

                if search_terms:
                    combined_query = " ".join(search_terms)
                    results = self.embeddings_service.query_embeddings_by_text(
                        combined_query)
                    if len(results) > size:
                        results = results[:size]
                else:
                    results = []

                if not results:
                    st.toast(
                        "Nenhum resultado encontrado com os critérios.",
                        icon="📭"
                    )
                    self._display_search_tips()
                    return

                # Mostrar critérios aplicados
                criteria = []
                if query:
                    criteria.append(f"Texto: '{query}'")
                if theme:
                    criteria.append(f"Tema: {theme}")
                if platform:
                    criteria.append(f"Plataforma: {platform}")
                if origin:
                    criteria.append(f"Origem: {origin}")
                if author:
                    criteria.append(f"Autor: {author}")
                if created_after:
                    criteria.append(f"Após: {created_after}")
                if created_before:
                    criteria.append(f"Antes: {created_before}")

                if criteria:
                    st.success(f"**Critérios:** {' • '.join(criteria)}")

                self._display_search_statistics(results, "busca avançada")
                self._display_search_results(results, show_metadata=True)

            except Exception as e:
                logger.error(f"Error during advanced search: {e}")
                st.toast("Erro durante a busca avançada", icon="❌")

    def _display_search_tips(self):
        """
        Exibe dicas para melhorar a busca
        """
        st.markdown("""
        **💡 Dicas para melhorar sua busca:**
        - Use palavras-chave mais específicas
        - Tente termos relacionados ou sinônimos
        - Verifique a ortografia
        - Experimente filtros de metadados mais amplos
        - Use a busca textual se não encontrar por metadados
        """)

    def _display_search_statistics(self, results: List[Dict], query: str):
        """
        Exibe estatísticas da busca

        Parameters
        ----------
        results : List[Dict]
            Resultados da busca
        query : str
            Consulta original
        """
        # Contar por tipo e índice
        type_counts: Dict[str, int] = {}
        index_counts: Dict[str, int] = {}

        for result in results:
            result_type = result.get('type', 'Desconhecido')
            result_index = result.get('index', 'unknown')

            type_counts[result_type] = type_counts.get(result_type, 0) + 1
            index_counts[result_index] = index_counts.get(result_index, 0) + 1

        # Análise de relevância
        scores = [r.get('score', 0) for r in results if r.get('score', 0) > 0]
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0

        # Escapar HTML da consulta para evitar problemas de renderização
        escaped_query = html.escape(str(query))

        # Exibir estatísticas
        st.success(f"""
        **Resultados para:** "{escaped_query}"

        **Total:** {
            len(results)
        } | **Relevância máxima:** {
            max_score:.1f
        } | **Relevância média:** {avg_score:.1f}
        """)

        # Distribuição por tipo
        cols = st.columns(len(type_counts))
        for i, (tipo, count) in enumerate(type_counts.items()):
            with cols[i]:
                st.metric(
                    label=tipo,
                    value=count,
                    help=f"Resultados do tipo: {tipo}"
                )

    def _display_search_results(
        self,
        results: List[Dict],
        show_metadata: bool
    ):
        """
        Exibe os resultados de busca formatados com suporte a metadados

        Parameters
        ----------
        results : List[Dict]
            Resultados da busca
        show_metadata : bool
            Se deve exibir metadados detalhados
        """
        st.markdown("### 📋 Resultados Detalhados")

        if show_metadata:
            # Opção de visualização
            col_view, col_sort = st.columns([2, 2])

            with col_view:
                view_mode = st.selectbox(
                    "Modo de visualização:",
                    ["Compacto", "Detalhado", "Metadados Completos"],
                    key="results_view_mode"
                )

            with col_sort:
                sort_by = st.selectbox(
                    "Ordenar por:",
                    ["Relevância", "Data", "Autor", "Plataforma"],
                    key="results_sort"
                )

            # Aplicar ordenação
            if sort_by == "Data":
                results.sort(
                    key=lambda x: x.get('created_at', ''), reverse=True
                )
            elif sort_by == "Autor":
                results.sort(key=lambda x: x.get('author', ''))
            elif sort_by == "Plataforma":
                results.sort(key=lambda x: x.get('platform', ''))
            # Relevância já vem ordenada por padrão

        # Agrupar por tipo para melhor organização
        results_by_type: Dict[str, List[Dict]] = {}
        for result in results:
            result_type = result.get('type', 'Post Gerado')
            if result_type not in results_by_type:
                results_by_type[result_type] = []
            results_by_type[result_type].append(result)

        # Ordenar cada grupo por score se não foi aplicada outra ordenação
        if not show_metadata or sort_by == "Relevância":
            for tipo in results_by_type:
                results_by_type[tipo].sort(
                    key=lambda x: x.get('score', 0),
                    reverse=True
                )

        # Exibir resultados por tipo
        for result_type, type_results in results_by_type.items():

            # Cabeçalho do tipo com ícones apropriados
            type_icons = {
                'Post Gerado': '📝',
                'Consultoria Comercial': '💼',
                'Reunião de Consultores': '🤝',
                'Base de Conhecimento': '📚',
                'Embedding': '🧠'
            }
            icon = type_icons.get(result_type, '📄')

            # Escapar HTML do tipo de resultado
            escaped_result_type = html.escape(str(result_type))

            st.info(f"""
            **{icon} {escaped_result_type}** ({len(type_results)} resultados)
            """)

            # Resultados do tipo
            for i, result in enumerate(type_results, 1):
                if show_metadata:
                    self._display_enhanced_result(
                        result, i, result_type, view_mode if (
                            show_metadata
                        ) else "Compacto"
                    )
                else:
                    self._display_single_result(result, i, result_type)

    def _display_single_result(
        self,
        result: Dict,
        index: int,
        result_type: str
    ):
        """
        Exibe um resultado individual

        Parameters
        ----------
        result : Dict
            Dados do resultado
        index : int
            Índice do resultado
        result_type : str
            Tipo do resultado
        """
        # Cores por tipo de resultado definidas (para uso futuro)

        # Extrair e escapar dados para HTML
        title = html.escape(str(result.get('title', 'Sem título')))
        content = html.escape(str(result.get('content', '')))
        score = result.get('score', 0)
        author = html.escape(str(result.get('author', '')))
        created_at = html.escape(str(result.get('created_at', '')))

        # Dados específicos por tipo (também escapados)
        extra_info = []
        if result.get('cliente'):
            cliente_escaped = html.escape(str(result.get('cliente')))
            extra_info.append(f"Cliente: {cliente_escaped}")
        if result.get('produto_ofertado'):
            produto_escaped = html.escape(str(result.get('produto_ofertado')))
            extra_info.append(f"Produto: {produto_escaped}")
        if result.get('resumo'):
            resumo_escaped = html.escape(str(result.get('resumo', ''))[:100])
            extra_info.append(f"Resumo: {resumo_escaped}...")
        if result.get('tags'):
            tags = result.get('tags', [])
            if isinstance(tags, list):
                tags_escaped = [html.escape(str(tag)) for tag in tags[:3]]
                extra_info.append(f"Tags: {', '.join(tags_escaped)}")

        # Truncar conteúdo para prévia (após escape HTML)
        content_preview = content[:400] + "..." if len(content) > 400 else (
            content
        )

        # Truncar título também
        title_display = title[:100] + "..." if len(title) > 100 else title

        # Preparar informações extras escapadas
        extra_info_escaped = " • ".join(extra_info)

        # Card do resultado usando componentes nativos
        with st.container():
            col_title, col_score = st.columns([4, 1])

            with col_title:
                st.markdown(f"**{index}. {title_display}**")

            with col_score:
                if score >= 0.8:
                    st.success(f"{score:.2f}")
                elif score >= 0.6:
                    st.warning(f"{score:.2f}")
                else:
                    st.info(f"{score:.2f}")

            if author or created_at:
                st.caption(
                    f"""{
                        author if author else ''
                    }{' • ' + created_at if created_at else ''}""")

            if extra_info_escaped:
                st.caption(extra_info_escaped)

            st.text_area(
                "Conteúdo:",
                value=content_preview,
                height=150,
                disabled=True,
                label_visibility="collapsed",
                key=f"content_{index}_{result_type}"
            )

            st.divider()

    def _display_enhanced_result(
        self,
        result: Dict,
        index: int,
        result_type: str,
        view_mode: str = "Detalhado"
    ):
        """
        Exibe um resultado individual com metadados aprimorados

        Parameters
        ----------
        result : Dict
            Dados do resultado
        index : int
            Índice do resultado
        result_type : str
            Tipo do resultado
        view_mode : str
            Modo de visualização (Compacto, Detalhado, Metadados Completos)
        """
        # Extrair dados principais
        title = html.escape(str(result.get('title', 'Sem título')))
        content = html.escape(
            str(result.get('content', result.get('text', '')))
        )
        score = result.get('score', 0)

        # Extrair metadados
        metadata = result.get('metadata', {})

        # Informações básicas
        author = html.escape(
            str(result.get('author', metadata.get('author', '')))
        )
        platform = html.escape(
            str(result.get('platform', metadata.get('platform_display', '')))
        )
        theme = html.escape(
            str(result.get('theme', metadata.get('theme', '')))
        )
        origin = html.escape(
            str(result.get('origin', metadata.get('origin', '')))
        )
        created_at = html.escape(str(result.get('created_at', '')))

        # Metadados específicos
        tags = html.escape(str(metadata.get('tags', '')))
        word_count = metadata.get('word_count', '')
        content_length = metadata.get('length', '')
        content_type = metadata.get('content_type', '')

        # Truncar conteúdo baseado no modo de visualização
        if view_mode == "Compacto":
            content_preview = content[:200] + "..." if len(
                content
            ) > 200 else content
            title_display = title[:80] + "..." if len(title) > 80 else title
        else:
            content_preview = content[:500] + "..." if len(
                content
            ) > 500 else content
            title_display = title[:120] + "..." if len(title) > 120 else title

        # Container principal do resultado
        with st.container():
            # Header com título e score
            col_title, col_score = st.columns([4, 1])

            with col_title:
                st.markdown(f"**{index}. {title_display}**")

            with col_score:
                if score >= 0.8:
                    st.success(f"🎯 {score:.3f}")
                elif score >= 0.6:
                    st.warning(f"🎯 {score:.3f}")
                else:
                    st.info(f"🎯 {score:.3f}")

            # Metadados principais em linha
            metadata_line = []
            if platform:
                metadata_line.append(f"📱 {platform}")
            if author:
                metadata_line.append(f"👤 {author}")
            if theme:
                metadata_line.append(f"🎯 {theme}")
            if origin:
                metadata_line.append(f"🗂️ {origin}")

            if metadata_line:
                st.caption(" • ".join(metadata_line))

            # Data de criação formatada
            if created_at and len(created_at) >= 10:
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(created_at[:10], '%Y-%m-%d')
                    br_date = date_obj.strftime('%d/%m/%Y')
                    st.caption(f"📅 {br_date}")
                except Exception:
                    st.caption(f"📅 {created_at[:10]}")

            # Conteúdo
            st.text_area(
                "Conteúdo:",
                value=content_preview,
                height=150 if view_mode != "Compacto" else 100,
                disabled=True,
                label_visibility="collapsed",
                key=f"""enhanced_content_{index}_{result_type}_{hash(str(
                    result.get('id', index)))}"""
            )

            # Metadados adicionais baseados no modo de visualização
            if view_mode == "Detalhado" or view_mode == "Metadados Completos":

                if tags or word_count or content_length:
                    col_meta1, col_meta2, col_meta3 = st.columns(3)

                    with col_meta1:
                        if tags:
                            st.caption(f"🏷️ **Tags:** {tags}")

                    with col_meta2:
                        if word_count:
                            st.caption(f"📊 **Palavras:** {word_count}")

                    with col_meta3:
                        if content_length:
                            st.caption(f"📏 **Tamanho:** {content_length}")

            # Modo "Metadados Completos" - mostra tudo em expandir
            if view_mode == "Metadados Completos":
                with st.expander(
                    f"🔍 Metadados Completos - Resultado {index}",
                    expanded=False
                ):
                    col_complete1, col_complete2 = st.columns(2)

                    with col_complete1:
                        st.markdown("**📋 Dados Básicos:**")
                        st.markdown(f"- **ID:** {result.get('id', 'N/A')}")
                        st.markdown(f"- **Tipo:** {result_type}")
                        st.markdown(
                            f"- **Índice:** {result.get('index', 'N/A')}"
                        )
                        st.markdown(f"- **Score:** {score:.4f}")
                        if content_type:
                            st.markdown(f"- **Tipo Conteúdo:** {content_type}")

                    with col_complete2:
                        st.markdown("**🔧 Metadados Técnicos:**")
                        st.markdown(f"""- **Dimensão Vetor:** {
                            result.get('vector_dimension', 'N/A')
                        }""")
                        st.markdown(
                            f"""- **Atualizado:** {
                                result.get(
                                    'updated_at',
                                    'N/A'
                                )[:10] if result.get(
                                    'updated_at'
                                ) else 'N/A'}"""
                        )
                        st.markdown(
                            f"""- **Código Plataforma:** {
                                metadata.get(
                                    'platform_code',
                                    metadata.get(
                                        'platform',
                                        'N/A'))}""")

                        # Exibir metadados originais se disponíveis
                        original_metadata = metadata.get(
                            'original_metadata', {})
                        if original_metadata and len(original_metadata) > 0:
                            st.markdown("**🗂️ Metadados Originais:**")
                            for key, value in original_metadata.items():
                                if value and str(value).strip():
                                    st.markdown(
                                        f"""- **{
                                            key
                                        }:** {
                                            str(value)[:50]
                                        }{'...' if len(
                                            str(value)
                                        ) > 50 else ''}"""
                                    )

            st.divider()

    def main_interface(self):
        """
        Interface principal de busca
        """
        st.title("Busca Inteligente")
        st.caption("Pesquise em nossa base de conhecimento")

        self.display_search_interface()
