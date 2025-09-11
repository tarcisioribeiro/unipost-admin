import streamlit as st
from typing import List, Dict
import logging
import html

logger = logging.getLogger(__name__)


class SearchResults:
    """
    Classe para exibir resultados de busca dos múltiplos índices Elasticsearch
    """

    def __init__(self):
        pass  # ElasticsearchService não está mais sendo usado"

    def display_search_interface(self):
        """
        Interface de busca para o usuário
        """
        st.subheader("🔍 Busca na Base de Conhecimento")

        # Verificar conexão
        if not self.es_service.is_connected():
            st.toast("Não foi possível conectar ao Elasticsearch", icon="❌")
            return

        # Interface de busca
        col_search, col_button = st.columns([3, 1])

        with col_search:
            search_query = st.text_input(
                "Digite sua consulta:",
                placeholder="Ex: marketing digital, vendas, consultoria...",
                help="Busque por temas, estratégias, ou palavras-chave",
                key="search_knowledge_base"
            )

        with col_button:
            st.markdown("<br>", unsafe_allow_html=True)  # Espaçamento
            search_button = st.button(
                "🔍 Buscar",
                type="primary",
                use_container_width=True,
                help="Buscar nos bancos de dados"
            )

        # Configurações avançadas (opcionais)
        with st.expander("⚙️ Configurações Avançadas", expanded=False):
            col_size, col_filter = st.columns(2)

            with col_size:
                result_size = st.slider(
                    "Número máximo de resultados:",
                    min_value=5,
                    max_value=50,
                    value=20,
                    step=5,
                    help="Quantidade de resultados por índice"
                )

            with col_filter:
                index_filter = st.multiselect(
                    "Filtrar por tipo de conteúdo:",
                    options=[
                        "Consultoria Comercial",
                        "Reunião de Consultores",
                        "Base de Conhecimento"
                    ],
                    default=[
                        "Consultoria Comercial",
                        "Reunião de Consultores",
                        "Base de Conhecimento"
                    ],
                    help="Selecione os tipos de conteúdo desejados"
                )

        # Executar busca
        if search_button and search_query.strip():
            self._perform_search(
                search_query.strip(),
                result_size,
                index_filter
            )
        elif search_button and not search_query.strip():
            st.toast("Por favor, digite uma consulta para buscar.", icon="⚠️")

    def _perform_search(self, query: str, size: int, type_filter: List[str]):
        """
        Executa a busca e exibe os resultados

        Parameters
        ----------
        query : str
            Consulta de busca
        size : int
            Número máximo de resultados
        type_filter : List[str]
            Filtros de tipo de conteúdo
        """
        with st.spinner(f"🔍 Buscando por '{query}'..."):
            try:
                # Executar busca
                results = []  # self.es_service.search_texts(query, size=size)

                if not results:
                    st.toast(
                        "Nenhum resultado encontrado para sua consulta.",
                        icon="📭"
                    )
                    st.markdown("""
                    **💡 Dicas para melhorar sua busca:**
                    - Use palavras-chave mais específicas
                    - Tente termos relacionados ou sinônimos
                    - Verifique a ortografia
                    - Use termos em português
                    """)
                    return

                # Filtrar por tipo se especificado
                if type_filter:
                    filtered_results = [
                        r for r in results
                        if r.get('type', '') in type_filter
                    ]

                    if filtered_results != results:
                        results = filtered_results
                        if not results:
                            st.toast(
                                "Nenhum resultado encontrado com os filtros.",
                                icon="⚠️"
                            )
                            return

                # Exibir estatísticas
                self._display_search_statistics(results, query)

                # Exibir resultados
                self._display_search_results(results)

            except Exception as e:
                logger.error(f"Error during search: {e}")
                st.toast("Erro durante a busca", icon="❌")

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
        st.markdown(f"""
        <div style="background: #f0f0f0; padding: 15px; 
                    border-left: 4px solid #333; margin-bottom: 15px;">
            <h3 style="margin: 0;">Resultados para: "{escaped_query}"</h3>
            <p style="margin: 8px 0;">
                Total: {len(results)} | 
                Relevância máxima: {max_score:.1f} | 
                Relevância média: {avg_score:.1f}
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Distribuição por tipo
        cols = st.columns(len(type_counts))
        for i, (tipo, count) in enumerate(type_counts.items()):
            with cols[i]:
                st.metric(
                    label=tipo,
                    value=count,
                    help=f"Resultados do tipo: {tipo}"
                )

    def _display_search_results(self, results: List[Dict]):
        """
        Exibe os resultados de busca formatados

        Parameters
        ----------
        results : List[Dict]
            Resultados da busca
        """
        st.markdown("### 📋 Resultados Detalhados")

        # Agrupar por tipo para melhor organização
        results_by_type: Dict[str, List[Dict]] = {}
        for result in results:
            result_type = result.get('type', 'Outros')
            if result_type not in results_by_type:
                results_by_type[result_type] = []
            results_by_type[result_type].append(result)

        # Ordenar cada grupo por score
        for tipo in results_by_type:
            results_by_type[tipo].sort(
                key=lambda x: x.get('score', 0),
                reverse=True
            )

        # Exibir resultados por tipo
        for result_type, type_results in results_by_type.items():

            # Cabeçalho do tipo
            type_icons = {
                'Consultoria Comercial': '💼',
                'Reunião de Consultores': '🤝',
                'Base de Conhecimento': '📚'
            }
            icon = type_icons.get(result_type, '📄')

            # Escapar HTML do tipo de resultado
            escaped_result_type = html.escape(str(result_type))

            st.markdown(f"""
            <div style="
                background: #f8f9fa;
                padding: 10px 15px;
                border-radius: 8px;
                border-left: 4px solid #007bff;
                margin: 20px 0 10px 0;
            ">
                <h4 style="margin: 0; color: #333;">
                    {icon} {escaped_result_type} ({
                len(type_results)
            } resultados)
                </h4>
            </div>
            """, unsafe_allow_html=True)

            # Resultados do tipo
            for i, result in enumerate(type_results[:10], 1):
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
        # Definir cores por tipo
        type_colors = {
            'Consultoria Comercial': '#28a745',
            'Reunião de Consultores': '#007bff',
            'Base de Conhecimento': '#6f42c1',
            'Outros': '#6c757d'
        }
        color = type_colors.get(result_type, '#6c757d')

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

        # Card do resultado
        with st.container():
            st.markdown(f"""
            <div style="border: 1px solid #ddd; padding: 15px; 
                        margin-bottom: 12px; border-left: 3px solid {color};">
                <div style="display: flex; justify-content: space-between; 
                            margin-bottom: 8px;">
                    <h5 style="margin: 0;">{index}. {title_display}</h5>
                    <span style="background: {color}; color: white; 
                                 padding: 2px 6px;">{score:.2f}</span>
                </div>
                
                <div style="color: #666; font-size: 13px; margin-bottom: 8px;">
                    {f'{author}' if author else ''} 
                    {f' • {created_at}' if created_at else ''}
                </div>
                
                {f'<div style="color: #555; font-size: 12px; margin-bottom: 8px;">{extra_info_escaped}</div>' if extra_info_escaped else ''}

                <div style="background: #f5f5f5; padding: 12px; 
                            max-height: 150px; overflow-y: auto;">
                    {content_preview}
                </div>
            </div>
            """, unsafe_allow_html=True)

    def main_interface(self):
        """
        Interface principal de busca
        """
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2>Busca Inteligente</h2>
            <p style="color: #666;">
                Pesquise em nossa base de conhecimento
            </p>
        </div>
        """, unsafe_allow_html=True)

        self.display_search_interface()
