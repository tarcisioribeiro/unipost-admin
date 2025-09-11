import streamlit as st
from services.embeddings_service import EmbeddingsService
from services.redis_service import RedisService
import logging

logger = logging.getLogger(__name__)


class ConfigModule:
    """
    Módulo de consultas no sistema.
    Permite consultar dados no Redis e embeddings na API.
    """

    def __init__(self):
        """Inicializa o módulo de consultas."""
        self.embeddings_service = EmbeddingsService()
        self.redis_service = RedisService()

    def query_redis(self, token, permissions):
        """
        Interface para consulta de dados no Redis.

        Parameters
        ----------
        token : str
            Token de autenticação do usuário
        permissions : list
            Lista de permissões do usuário
        """
        # Layout em duas colunas: Parâmetros | Resultado
        col_params, col_result = st.columns([1.0, 1.2])

        with col_params:
            st.subheader("🔍 Consulta Redis")

            # Campo de palavra-chave
            search_keyword = st.text_input(
                label="🔎 Palavra-chave",
                placeholder="Ex: embeddings, cache, search...",
                help="Digite uma palavra-chave para buscar no Redis",
                key="redis_search_input"
            )

            # Opções avançadas
            with st.expander("⚙️ Opções Avançadas", expanded=False):
                search_pattern = st.selectbox(
                    "Padrão de busca:",
                    [
                        "Contém a palavra",
                        "Prefixo exato",
                        "Sufixo exato",
                        "Palavra exata"
                    ],
                    help="Como aplicar a busca na palavra-chave"
                )

                max_results = st.slider(
                    "Máximo de resultados:",
                    min_value=10,
                    max_value=100,
                    value=20,
                    step=5,
                    help="Limite de resultados a exibir"
                )

            # Botão de busca
            search_button = st.button(
                "🔍 Buscar no Redis",
                use_container_width=True,
                type="primary",
                key="redis_search_btn",
                help="Executar busca no Redis"
            )

        # Área de resultado
        with col_result:
            result_container = st.container()

            # Estado inicial
            if not search_button and 'redis_last_search' not in (
                st.session_state
            ):
                with result_container:
                    st.markdown("""
                    <div style="
                        background: #f8f9fa;
                        padding: 40px;
                        border-radius: 15px;
                        border: 2px dashed #dee2e6;
                        text-align: center;
                        min-height: 400px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                    ">
                        <h3 style="color: #6c757d;">📊 Resultados Redis</h3>
                        <p style="color: #6c757d;">
                            Os resultados da busca aparecerão aqui
                        </p>
                        <div style="margin-top: 20px; font-size: 48px;">
                            🔍
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Exibir último resultado se existe
            elif 'redis_last_search' in st.session_state:
                self._display_redis_results(
                    result_container,
                    st.session_state['redis_last_search']
                )

            # Processar busca se botão foi clicado
            if search_button:
                if not search_keyword or not search_keyword.strip():
                    st.toast("Por favor, digite uma palavra-chave!", icon="⚠️")
                else:
                    self._process_redis_search(
                        result_container,
                        search_keyword.strip(),
                        search_pattern,
                        max_results
                    )

    def query_embeddings(self, token, permissions):
        """
        Interface simplificada para consulta de embeddings na API.

        Parameters
        ----------
        token : str
            Token de autenticação do usuário
        permissions : list
            Lista de permissões do usuário
        """
        # Layout centralizado e simplificado
        col_center = st.columns([1, 3, 1])[1]
        result_container = st.container()

        with col_center:
            st.subheader("🧠 Consulta de Embeddings")
            st.markdown(
                "**Digite um texto e receba os vetores que contenham ele.**"
            )

            # Campo de busca simplificado e maior
            search_keyword = st.text_input(
                label="",
                placeholder="Digite o texto que deseja buscar nos embeddings",
                key="embeddings_search_input",
                label_visibility="collapsed"
            )

            # Botão de busca centralizado
            col_btn = st.columns([1, 1, 1])[1]
            with col_btn:
                search_button = st.button(
                    "🔍 Buscar",
                    use_container_width=True,
                    type="primary",
                    key="embeddings_search_btn"
                )

        # Estado inicial - mostrar mensagem quando não há busca
        if not search_button and 'embeddings_last_search' not in (
            st.session_state
        ):
            st.markdown("""
            <div style="
                background: #f8f9fa;
                padding: 30px;
                border-radius: 15px;
                border: 2px dashed #dee2e6;
                text-align: center;
                margin: 30px 0;
            ">
                <div style="font-size: 48px; margin-bottom: 20px;">🤖</div>
                <h3 style="color: #6c757d; margin-bottom: 10px;">
                    Busca de Embeddings
                </h3>
                <p style="color: #6c757d;">
                    Digite um texto acima para encontrar todos os vetores
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Exibir último resultado se existe
        elif 'embeddings_last_search' in st.session_state:
            self._display_embeddings_results(
                result_container,
                st.session_state['embeddings_last_search']
            )

        # Processar busca se botão foi clicado
        if search_button:
            if not search_keyword or not search_keyword.strip():
                st.toast("Por favor, digite um texto para buscar!", icon="⚠️")
            else:
                # Usar valores padrão simplificados
                self._process_embeddings_search(
                    result_container,
                    search_keyword.strip(),
                    origin=None,  # Buscar em todas as origens
                    max_results=20,  # Padrão de 20 resultados
                    token=token
                )

    def _process_redis_search(
            self,
            result_container,
            keyword,
            pattern,
            max_results
    ):
        """Processa busca no Redis e exibe resultados."""
        with result_container.container():
            st.markdown("""
            <div style="text-align: center; margin: 20px 0;">
                <h3 style="color: #1f77b4; margin: 0;">🔍 Buscando no Redis</h3>
                <p style="color: #666; margin: 5px 0;">
                    Processando sua consulta...
                </p>
            </div>
            """, unsafe_allow_html=True)

            progress_bar = st.progress(0)
            status_text = st.empty()

        try:
            status_text.text("🔍 Buscando chaves no Redis...")
            progress_bar.progress(30)

            # Buscar no Redis baseado no padrão
            if pattern == "Prefixo exato":
                search_pattern = f"{keyword}*"
            elif pattern == "Sufixo exato":
                search_pattern = f"*{keyword}"
            elif pattern == "Palavra exata":
                search_pattern = keyword
            else:  # Contém a palavra
                search_pattern = f"*{keyword}*"

            redis_keys = self.redis_service.get_all_keys(search_pattern)

            progress_bar.progress(70)
            status_text.text(f"✅ Encontradas {len(redis_keys)} chaves")

            if redis_keys:
                # Limitar resultados
                limited_keys = redis_keys[:max_results]

                # Obter valores das chaves
                results = []
                for key in limited_keys:
                    try:
                        value = self.redis_service.get_key_value(key)
                        key_type = self.redis_service.get_key_type(key)
                        ttl = self.redis_service.get_key_ttl(key)

                        results.append({
                            'key': key,
                            'value': value,
                            'type': key_type,
                            'ttl': ttl
                        })
                    except Exception:
                        results.append({
                            'key': key,
                            'value': 'Erro ao ler',
                            'type': 'unknown',
                            'ttl': -1
                        })
            else:
                results = []

            progress_bar.progress(100)
            status_text.text("✅ Busca concluída!")

            # Salvar na sessão
            st.session_state['redis_last_search'] = {
                'keyword': keyword,
                'pattern': pattern,
                'results': results,
                'total_found': len(redis_keys)
            }

            # Limpar progresso
            progress_bar.empty()
            status_text.empty()

            # Exibir resultados
            self._display_redis_results(
                result_container,
                st.session_state['redis_last_search']
            )

        except Exception as e:
            st.toast(f"Erro na busca: {str(e)}", icon="❌")
            logger.error(f"Erro na busca Redis: {e}")

        finally:
            try:
                progress_bar.empty()
                status_text.empty()
            except Exception:
                pass

    def _process_embeddings_search(
            self,
            result_container,
            keyword,
            origin,
            max_results,
            token
    ):
        """Processa busca de embeddings e exibe resultados."""
        with result_container.container():
            st.markdown("""
            <div style="text-align: center; margin: 20px 0;">
                <h3 style="color: #1f77b4; margin: 0;">
                    🧠 Buscando Embeddings
                </h3>
                <p style="color: #666; margin: 5px 0;">Consultando API...</p>
            </div>
            """, unsafe_allow_html=True)

            progress_bar = st.progress(0)
            status_text = st.empty()

        try:
            status_text.text("🔍 Consultando API de embeddings...")
            progress_bar.progress(50)

            # Buscar embeddings usando o novo método que consulta
            # todas as colunas
            results = self.embeddings_service.search_all_embeddings_like(
                keyword,
                max_results
            )

            progress_bar.progress(100)
            status_text.text(f"✅ Encontrados {len(results)} embeddings")

            # Filtrar por origem se especificado
            if origin and results:
                results = [
                    r for r in results if r.get(
                        'metadata',
                        {}
                    ).get('origin') == origin
                ]

            # Salvar na sessão
            st.session_state['embeddings_last_search'] = {
                'keyword': keyword,
                'origin': origin,
                'results': results,
                'total_found': len(results)
            }

            # Limpar progresso
            progress_bar.empty()
            status_text.empty()

            # Exibir resultados
            self._display_embeddings_results(
                result_container,
                st.session_state['embeddings_last_search']
            )

        except Exception as e:
            st.toast(f"Erro na busca: {str(e)}", icon="❌")
            logger.error(f"Erro na busca embeddings: {e}")

        finally:
            try:
                progress_bar.empty()
                status_text.empty()
            except Exception:
                pass

    def _display_redis_results(self, container, search_data):
        """Exibe resultados da busca Redis."""
        with container.container():
            results = search_data.get('results', [])
            keyword = search_data.get('keyword', '')
            total_found = search_data.get('total_found', 0)

            # Cabeçalho
            st.markdown(f"""
            <div style="background: #f0f0f0; padding: 12px; border-left: 4px solid #333;">
                <h4 style="margin: 0;">Redis: "{keyword}"</h4>
                <p style="margin: 5px 0;">{total_found} chaves encontradas</p>
            </div>
            """, unsafe_allow_html=True)

            if not results:
                st.warning("🔍 Nenhuma chave encontrada.")
                return

            # Cards otimizados e responsivos
            for result in results:
                key = result['key']
                value = str(result['value'])[:300] + ('...' if len(
                    str(result['value'])
                ) > 300 else '')
                key_type = result['type']
                ttl = result['ttl']

                ttl_text = "Sem expiração" if ttl == -1 else f"{ttl}s" if (
                    ttl > 0
                ) else "Expirada"

                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 10px; margin: 4px 0;">
                    <div style="display: flex; justify-content: space-between; 
                                margin-bottom: 8px;">
                        <strong>{key}</strong>
                        <span style="background: #333; color: white; padding: 2px 6px;">
                            {key_type.upper()}
                        </span>
                    </div>
                    <div style="background: #f5f5f5; padding: 8px; 
                                font-family: monospace; font-size: 12px; 
                                max-height: 80px; overflow-y: auto;">
                        {value}
                    </div>
                    <small style="color: #666;">{ttl_text}</small>
                </div>
                """, unsafe_allow_html=True)

            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Exibidas", len(results))
            with col2:
                st.metric("Total", total_found)
            with col3:
                unique_types = len(set(r['type'] for r in results))
                st.metric("Tipos", unique_types)

    def _display_embeddings_results(self, container, search_data):
        """Exibe resultados da busca de embeddings mostrando
        todas as colunas."""
        with container.container():
            results = search_data.get('results', [])
            keyword = search_data.get('keyword', '')
            total_found = search_data.get('total_found', 0)

            # Cabeçalho
            st.markdown(f"""
            <div style="background: #f0f0f0; padding: 12px; border-left: 4px solid #333;">
                <h4 style="margin: 0;">Busca: "{keyword}"</h4>
                <p style="margin: 5px 0;">{total_found} embeddings encontrados</p>
            </div>
            """, unsafe_allow_html=True)

            if not results:
                st.warning("🧠 Nenhum embedding encontrado.")
                return

            # Cards de embeddings com todas as colunas
            for i, result in enumerate(results, 1):
                # Dados principais
                embedding_id = result.get('id', 'N/A')
                title = result.get('title', 'Sem título')
                content = result.get('content', 'Sem conteúdo')
                origin = result.get('origin', 'N/A')
                created_at = result.get('created_at', 'N/A')
                updated_at = result.get('updated_at', 'N/A')
                vector_dimension = result.get('vector_dimension', 'N/A')
                # Metadata
                metadata = result.get('metadata', {})
                theme = (
                    metadata.get('theme', 'N/A')
                    if isinstance(metadata, dict) else 'N/A'
                )
                platform_display = (
                    metadata.get('platform_display', 'N/A')
                    if isinstance(metadata, dict) else 'N/A'
                )
                author = (
                    metadata.get('author', 'N/A')
                    if isinstance(metadata, dict) else 'N/A'
                )
                tags = (
                    metadata.get('tags', 'N/A')
                    if isinstance(metadata, dict) else 'N/A'
                )
                length = (
                    metadata.get('length', 'N/A')
                    if isinstance(metadata, dict) else 'N/A'
                )
                word_count = (
                    metadata.get('word_count', 'N/A')
                    if isinstance(metadata, dict) else 'N/A'
                )

                # Conteúdo truncado para exibição
                display_content = (
                    content[:200] + ('...' if len(content) > 200 else '')
                )

                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 12px; margin: 8px 0;">
                    <div style="display: flex; margin-bottom: 10px;">
                        <span style="background: #333; color: white; 
                                     padding: 2px 6px; margin-right: 8px;">
                            {i}
                        </span>
                        <strong>ID: {embedding_id} | {title}</strong>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; 
                                gap: 8px; font-size: 13px; margin-bottom: 10px;">
                        <div><strong>Origem:</strong> {origin}</div>
                        <div><strong>Tema:</strong> {theme}</div>
                        <div><strong>Plataforma:</strong> {platform_display}</div>
                        <div><strong>Autor:</strong> {author}</div>
                        <div><strong>Criado:</strong> {created_at[:10] if created_at != 'N/A' else 'N/A'}</div>
                        <div><strong>Atualizado:</strong> {updated_at[:10] if updated_at != 'N/A' else 'N/A'}</div>
                        <div><strong>Dimensão:</strong> {vector_dimension}</div>
                        <div><strong>Palavras:</strong> {word_count}</div>
                        <div><strong>Tamanho:</strong> {length}</div>
                        <div><strong>Tags:</strong> {tags}</div>
                    </div>

                    <div style="background: #f5f5f5; padding: 10px; 
                                border-left: 3px solid #333;">
                        <strong>Conteúdo:</strong><br>{display_content}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Resumo detalhado
            if results:
                # Estatísticas
                total_embeddings = len(results)
                unique_origins = len(set(r.get('origin', 'N/A')
                                     for r in results))
                unique_themes = len(set(r.get('metadata', {}).get(
                    'theme', 'N/A') for r in results if isinstance(r.get('metadata', {}), dict)))
                unique_platforms = len(set(r.get('metadata', {}).get(
                    'platform_display', 'N/A') for r in results if isinstance(r.get('metadata', {}), dict)))

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📊 Total", total_embeddings)
                with col2:
                    st.metric("🗂️ Origens", unique_origins)
                with col3:
                    st.metric("🎯 Temas", unique_themes)
                with col4:
                    st.metric("📱 Plataformas", unique_platforms)

    def check_permissions(self, user_permissions: list) -> bool:
        """Verifica se o usuário tem permissões para acessar consultas."""
        required_permissions = [
            'admin', 'config', 'read',
            'texts.view_text', 'texts.add_text',
            'texts.change_text', 'texts.delete_text'
        ]
        return any(perm in user_permissions for perm in required_permissions)

    def render_access_denied(self):
        """Renderiza mensagem de acesso negado."""
        st.error("🔒 Acesso Restrito")
        st.markdown("""
        ### Permissões Insuficientes

        Você não possui permissão para acessar as consultas do sistema.

        **Permissões necessárias (qualquer uma):**
        - `admin` - Administrador do sistema
        - `config` - Acesso às configurações
        - `read` - Leitura básica
        - Permissões de texto (`texts.view_text`, `texts.add_text`, etc.)

        Entre em contato com o administrador do sistema para solicitar acesso.
        """)

    def main(self, user_permissions: list):
        """Ponto de entrada principal do módulo de consultas."""
        if not self.check_permissions(user_permissions):
            self.render_access_denied()
            return

        # Cabeçalho principal
        st.title("⚙️ Consultas do Sistema")
        st.markdown("Consulte dados armazenados no Redis e embeddings na API")

        # Menu superior com 3 colunas para seleção
        col1, col2, col3 = st.columns(3)

        with col2:  # Coluna central
            query_type = st.selectbox(
                "Escolha o tipo de consulta:",
                ["🔍 Consulta Redis", "🧠 Consulta Embeddings"],
                key="query_type_selector",
            )

        st.divider()

        # Renderizar interface baseada na seleção
        token = st.session_state.get('token', None)

        if query_type == "🔍 Consulta Redis":
            self.query_redis(token, user_permissions)
        else:
            self.query_embeddings(token, user_permissions)
