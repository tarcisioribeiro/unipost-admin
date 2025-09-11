import streamlit as st
import requests
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
from dictionary.vars import API_BASE_URL
import logging

logger = logging.getLogger(__name__)


class ElasticsearchMonitor:
    """
    Módulo para monitoramento e consulta do Elasticsearch.
    Permite visualizar dados, fazer consultas e verificar saúde do cluster.
    """

    def __init__(self):
        """Inicializa o monitor do Elasticsearch."""
        self.api_base_url = API_BASE_URL

    def check_elasticsearch_health(self) -> Dict[str, Any]:
        """
        Verifica a saúde do cluster Elasticsearch.

        Returns
        -------
        Dict[str, Any]
            Status de saúde do Elasticsearch
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/elasticsearch/health/",
                timeout=10
            )

            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "data": response.json(),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error checking Elasticsearch health: {e}")
            return {
                "status": "connection_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_cluster_info(self) -> Dict[str, Any]:
        """
        Obtém informações gerais do cluster Elasticsearch.

        Returns
        -------
        Dict[str, Any]
            Informações do cluster
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/elasticsearch/info/",
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return {"error": str(e)}

    def get_indices_info(self) -> List[Dict[str, Any]]:
        """
        Lista todos os índices disponíveis no Elasticsearch.

        Returns
        -------
        List[Dict[str, Any]]
            Lista de índices com suas informações
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/elasticsearch/indices/",
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return [{"error": f"HTTP {response.status_code}"}]

        except Exception as e:
            logger.error(f"Error getting indices info: {e}")
            return [{"error": str(e)}]

    def search_documents(
        self,
        index: str = "",
        query: str = "*",
        size: int = 10
    ) -> Dict[str, Any]:
        """
        Busca documentos no Elasticsearch.

        Parameters
        ----------
        index : str
            Nome do índice (vazio para buscar em todos)
        query : str
            Query de busca
        size : int
            Número de resultados

        Returns
        -------
        Dict[str, Any]
            Resultados da busca
        """
        try:
            params = {
                "q": query,
                "size": size
            }

            if index:
                params["index"] = index

            response = requests.get(
                f"{self.api_base_url}/elasticsearch/search/",
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return {"error": str(e)}

    def get_document_by_id(self, index: str, doc_id: str) -> Dict[str, Any]:
        """
        Obtém um documento específico pelo ID.

        Parameters
        ----------
        index : str
            Nome do índice
        doc_id : str
            ID do documento

        Returns
        -------
        Dict[str, Any]
            Documento encontrado
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/elasticsearch/document/",
                params={"index": index, "id": doc_id},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return {"error": str(e)}

    def render_health_status(self):
        """Renderiza o status de saúde do Elasticsearch."""
        st.subheader("🏥 Status de Saúde do Elasticsearch")

        with st.spinner("Verificando saúde do cluster..."):
            health_data = self.check_elasticsearch_health()

        if health_data["status"] == "healthy":
            st.success("✅ Elasticsearch está operacional")

            if "data" in health_data:
                health_info = health_data["data"]

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    cluster_status = health_info.get("status", "unknown")
                    status_color = {
                        "green": "🟢",
                        "yellow": "🟡",
                        "red": "🔴"
                    }.get(cluster_status, "⚫")
                    st.metric(
                        "Status do Cluster",
                        f"{status_color} {cluster_status}"
                    )

                with col2:
                    st.metric(
                        "Nós Ativos",
                        health_info.get("number_of_nodes", "N/A")
                    )

                with col3:
                    st.metric(
                        "Nós de Dados",
                        health_info.get(
                            "number_of_data_nodes",
                            "N/A"
                        )
                    )

                with col4:
                    st.metric(
                        "Shards Ativos",
                        health_info.get(
                            "active_shards",
                            "N/A"
                        )
                    )

                # Informações detalhadas em expandor
                with st.expander("📊 Informações Detalhadas"):
                    st.json(health_info)

        elif health_data["status"] == "error":
            st.error(f"❌ Erro na API: {health_data['error']}")

        else:
            st.error(f"❌ Erro de conexão: {health_data['error']}")

        st.caption(f"Última verificação: {health_data['timestamp']}")

    def render_indices_info(self):
        """Renderiza informações dos índices."""
        st.subheader("📚 Índices do Elasticsearch")

        with st.spinner("Carregando índices..."):
            indices = self.get_indices_info()

        if indices and not indices[0].get("error"):
            # Criar DataFrame para exibição
            indices_data = []
            for idx in indices:
                indices_data.append({
                    "Índice": idx.get("index", "N/A"),
                    "Status": idx.get("status", "N/A"),
                    "Documentos": idx.get("docs.count", "N/A"),
                    "Tamanho": idx.get("store.size", "N/A"),
                    "Shards": f"""
                        {idx.get('pri', 'N/A')}/{idx.get('rep', 'N/A')}"
                    """
                })

            if indices_data:
                df = pd.DataFrame(indices_data)
                st.dataframe(df, use_container_width=True)

                # Métricas resumidas
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total de Índices", len(indices_data))

                with col2:
                    total_docs = sum(
                        int(idx.get("docs.count", 0))
                        for idx in indices
                        if str(idx.get("docs.count", "")).isdigit()
                    )
                    st.metric("Total de Documentos", f"{total_docs:,}")

                with col3:
                    active_indices = sum(
                        1 for idx in indices
                        if idx.get("status") == "open"
                    )
                    st.metric("Índices Ativos", active_indices)
            else:
                st.info("Nenhum índice encontrado")
        else:
            error_msg = indices[0].get(
                "error",
                "Erro desconhecido"
            ) if indices else "Sem dados"
            st.error(f"❌ Erro ao carregar índices: {error_msg}")

    def render_search_interface(self):
        """Renderiza interface de busca."""
        st.subheader("🔍 Consulta de Documentos")

        # Parâmetros de busca
        col1, col2 = st.columns([2, 1])

        with col1:
            query = st.text_input(
                "Query de Busca",
                value="*",
                placeholder="ex: energia renovável, sustentabilidade",
                help="Use * para buscar todos os documentos"
            )

        with col2:
            size = st.number_input(
                "Quantidade de Resultados",
                min_value=1,
                max_value=100,
                value=10
            )

        # Seleção de índice
        with st.spinner("Carregando índices..."):
            indices = self.get_indices_info()

        index_options = ["Todos os índices"]
        if indices and not indices[0].get("error"):
            index_names = [
                idx.get(
                    "index",
                    ""
                ) for idx in indices if idx.get("index")]
            index_options.extend(sorted(index_names))

        selected_index = st.selectbox(
            "Índice",
            index_options,
            help="Selecione um índice específico ou busque em todos"
        )

        # Botão de busca
        if st.button("🔍 Buscar", type="primary", use_container_width=True):
            search_index = "" if (
                selected_index == "Todos os índices"
            ) else selected_index

            with st.spinner("Buscando documentos..."):
                results = self.search_documents(search_index, query, size)

            if "error" not in results:
                hits = results.get("hits", {})
                total_hits = hits.get("total", {})
                documents = hits.get("hits", [])

                # Informações da busca
                st.success("✅ Busca realizada com sucesso!")

                col1, col2, col3 = st.columns(3)
                with col1:
                    total_value = total_hits.get(
                        "value",
                        0
                    ) if isinstance(total_hits, dict) else total_hits
                    st.metric("Resultados Encontrados", f"{total_value:,}")

                with col2:
                    st.metric("Documentos Exibidos", len(documents))

                with col3:
                    max_score = hits.get("max_score", "N/A")
                    st.metric(
                        "Score Máximo",
                        f"{max_score:.3f}" if isinstance(
                            max_score, (int, float)
                        ) else max_score)

                # Exibir documentos
                if documents:
                    st.markdown("### 📄 Documentos Encontrados")

                    for i, doc in enumerate(documents, 1):
                        source = doc.get("_source", {})
                        score = doc.get("_score", "N/A")
                        doc_id = doc.get("_id", "N/A")
                        index_name = doc.get("_index", "N/A")

                        with st.expander(
                            f"""📄 Documento {i} (Score: {
                                score:.3f})""" if isinstance(
                                    score, (
                                        int,
                                        float
                                    )
                                ) else f"📄 Documento {i}"):
                            # Informações básicas
                            st.markdown(f"**ID:** `{doc_id}`")
                            st.markdown(f"**Índice:** `{index_name}`")
                            st.markdown(f"**Score:** {score}")

                            # Conteúdo do documento
                            st.markdown("**Conteúdo:**")

                            # Tentar mostrar campos mais relevantes primeiro
                            relevant_fields = [
                                "title",
                                "content",
                                "text",
                                "description"
                            ]
                            other_fields = []

                            for field in relevant_fields:
                                if field in source:
                                    value = source[field]
                                    if isinstance(
                                        value,
                                        str
                                    ) and len(value) > 200:
                                        st.markdown(
                                            f"""**{
                                                field.title()
                                            }:** {value[:200]}..."""
                                        )
                                    else:
                                        st.markdown(
                                            f"**{field.title()}:** {value}"
                                        )

                            # Outros campos
                            for key, value in source.items():
                                if key not in relevant_fields:
                                    other_fields.append((key, value))

                            if other_fields:
                                with st.expander("🔧 Outros Campos"):
                                    for key, value in other_fields:
                                        st.markdown(f"**{key}:** {value}")
                else:
                    st.info(
                        "Nenhum documento encontrado com os critérios de busca"
                    )

            else:
                st.error(f"❌ Erro na busca: {results['error']}")

    def render_document_viewer(self):
        """Renderiza visualizador de documento específico."""
        st.subheader("📄 Visualizador de Documento")

        col1, col2 = st.columns(2)

        with col1:
            index = st.text_input(
                "Nome do Índice",
                placeholder="ex: posts, consultores, unibrain"
            )

        with col2:
            doc_id = st.text_input(
                "ID do Documento",
                placeholder="ex: 123, abc-def-456"
            )

        if st.button(
            "📋 Buscar Documento",
            type="primary",
            use_container_width=True
        ):
            if not index or not doc_id:
                st.warning(
                    "⚠️ Por favor, preencha o índice e o ID do documento"
                )
                return

            with st.spinner("Buscando documento..."):
                result = self.get_document_by_id(index, doc_id)

            if "error" not in result:
                st.success("✅ Documento encontrado!")

                # Informações básicas
                doc_info = result.get("_source", {})

                st.markdown(f"**Índice:** `{result.get('_index', 'N/A')}`")
                st.markdown(f"**ID:** `{result.get('_id', 'N/A')}`")
                st.markdown(f"**Versão:** {result.get('_version', 'N/A')}")

                st.markdown("---")

                # Conteúdo formatado
                st.markdown("### 📋 Conteúdo do Documento")

                if doc_info:
                    # JSON formatado
                    st.json(doc_info)
                else:
                    st.info("Documento sem conteúdo _source")

            else:
                st.error(f"❌ Erro ao buscar documento: {result['error']}")

    def render_main_interface(self):
        """Renderiza interface principal do monitor."""
        st.title("🔍 Monitor do Elasticsearch")
        st.markdown(
            "Ferramenta para monitoramento e consulta do Elasticsearch"
        )

        # Tabs para diferentes funcionalidades
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏥 Saúde",
            "📚 Índices",
            "🔍 Buscar",
            "📄 Documento"
        ])

        with tab1:
            self.render_health_status()

        with tab2:
            self.render_indices_info()

        with tab3:
            self.render_search_interface()

        with tab4:
            self.render_document_viewer()
