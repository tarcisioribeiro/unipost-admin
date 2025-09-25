import streamlit as st
import pandas as pd
from texts.request import TextsRequest
from dictionary.vars import PLATFORMS
from services.embeddings_service import EmbeddingsService
from services.redis_service import RedisService
from services.text_generation_service import TextGenerationService
import logging

logger = logging.getLogger(__name__)


class Texts:
    """
    Classe que representa os métodos referentes à geração de post natural.
    Implementa o fluxo completo conforme nova arquitetura:
    - Busca de embeddings via API externa
    - Armazenamento no Redis
    - Interface para input do usuário
    - Elaboração de prompt com referências
    - Geração de post via LLM
    """

    def __init__(self):
        self.embeddings_service = EmbeddingsService()
        self.redis_service = RedisService()
        self.text_service = TextGenerationService()

    def treat_texts_dataframe(self, texts_data):
        """
        Realiza o tratamento e formatação dos dados referentes aos posts.

        Parameters
        ----------
        texts_data : list
            A série de dados referentes aos posts gerados.

        Returns
        -------
        df : DataFrame
            A série de dados tratados.
        """

        df = pd.DataFrame(texts_data)
        df = df.drop(columns=['id'])

        # Mapear campos da API para campos esperados pelo frontend
        if 'content' in df.columns and 'generated_text' not in df.columns:
            df['generated_text'] = df['content']

        # Mapear status baseado no campo is_approved da API
        if 'is_approved' in df.columns and 'status' not in df.columns:
            df['status'] = df['is_approved'].apply(
                lambda x: 'approved' if x else 'pending_approval')

        df = df.rename(
            columns={
                'theme': 'Tema',
                'generated_text': 'Post Gerado',
                'created_at': 'Data de Criação',
                'status': 'Status',
            }
        )

        df = df[[
            "Tema",
            "Post Gerado",
            "Data de Criação",
            "Status",
        ]
        ]

        df = df.sort_values(
            by="Data de Criação",
            ascending=False
        )

        return df

    def get_texts_index(self, texts):
        """
        Obtém o índice dos posts, com seus temas e identificadores.

        Parameters
        ----------
        texts : dict
            Dicionário com os dados dos posts.

        Returns
        -------
        texts_index : dict
            Dicionário com os índices.
        """
        texts_topics = []
        texts_ids = []

        for text in texts:
            texts_topics.append(text['theme'])
            texts_ids.append(text['id'])

        texts_index = dict(zip(texts_topics, texts_ids))

        return texts_index

    def validate_topic(self, topic):
        """
        Valida o tema informado (versão simplificada sem st.error visual).

        Parameters
        ----------
        topic : str
            O tema para geração de post.

        Returns
        -------
        bool
            se o tema informado é ou não válido.
        str
            O tema validado.
        """
        if not topic or len(topic.strip()) < 5:
            return False, topic

        if len(topic.strip()) > 500:
            return False, topic

        return True, topic.strip()

    def _process_text_generation_improved(
            self,
            user_topic: str,
            search_query: str,
            platform: str,
            tone: str,
            creativity_level: str,
            length: str,
            include_hashtags: bool,
            include_cta: bool,
            token: str,
            result_container):
        """
        Processa a geração completa de post seguindo o fluxo do roadmap.

        Parameters não utilizados mantidos para compatibilidade futura:
        - include_hashtags: bool
        - include_cta: bool
        """
        # Parâmetros mantidos para futura implementação
        _ = include_hashtags, include_cta
        # Interface de progresso simplificada
        with result_container.container():
            # Cabeçalho do processo
            st.header("🚀 Gerando Post")
            st.info("Processando...")

            # Container para progresso
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()

        try:
            # 1. Verificar cache Redis
            status_text.info("🔍 Verificando cache...")
            progress_bar.progress(10)

            cached_embeddings = self.redis_service.get_cached_embeddings(
                search_query
            )

            if cached_embeddings:
                similar_texts = cached_embeddings.get('similar_texts', [])
                status_text.success("✅ Cache encontrado")
            else:
                # 2. Busca via API de embeddings (por palavras individuais)
                status_text.text("🔍 Buscando referências...")
                progress_bar.progress(30)

                # Consultar por palavras individuais
                embeddings_by_word = self.embeddings_service.query_embeddings_by_individual_words(  # noqa: E501
                    search_query
                )

                # Agregar todos os resultados para manter compatibilidade
                raw_texts = []
                for _, word_embeddings in embeddings_by_word.items():
                    raw_texts.extend(word_embeddings)

                # Remover duplicatas baseado no ID
                seen_ids = set()
                unique_texts = []
                for text in raw_texts:
                    text_id = text.get('id', str(hash(str(text))))
                    if text_id not in seen_ids:
                        seen_ids.add(text_id)
                        unique_texts.append(text)

                raw_texts = unique_texts

                # Permite geração mesmo sem resultados da API
                if raw_texts:
                    # 3. Tratamento dos textos da API
                    status_text.text("⚙️ Processando textos...")
                    progress_bar.progress(50)

                    texts = self.text_service.treat_text_content(raw_texts)

                    if texts:
                        # 4. Busca de textos similares via API
                        status_text.text("🎯 Analisando similaridade...")
                        progress_bar.progress(70)

                        similar_texts = (
                            self.text_service.find_similar_texts_via_api(
                                user_topic,
                                texts
                            )
                        )

                        # 5. Cache no Redis
                        if similar_texts:
                            self.redis_service.cache_embeddings(
                                search_query, {'similar_texts': similar_texts})

                            # Simples confirmação de referências encontradas
                            count = len(similar_texts)
                            msg = f"✅ {count} referências encontradas"
                            status_text.success(msg)
                        else:
                            st.toast(
                                "Nenhuma referência encontrada",
                                icon="ℹ️"
                            )
                            similar_texts = []
                    else:
                        st.toast(
                            "Textos inválidos, prosseguindo sem referências",
                            icon="⚠️"
                        )
                        similar_texts = []
                else:
                    st.toast("Nenhuma referência encontrada", icon="ℹ️")
                    similar_texts = []

            # 6. Elaboração do contexto de prompt com novos parâmetros
            status_text.text("📝 Preparando prompt...")
            progress_bar.progress(80)

            prompt_context = self.text_service.create_prompt_context(
                user_topic,
                similar_texts,
                platform,
                tone,
                creativity_level,
                length
            )

            # 7. Geração de post via OpenAI/LLM
            status_text.text("🤖 Gerando post...")
            progress_bar.progress(90)

            generated_text = self.text_service.generate_text_via_llm(
                prompt_context
            )
            if not generated_text:
                st.toast("Erro na geração de post via IA", icon="❌")
                return

            # 8. Salvar no banco de dados da API UniPost (SEM EMBEDDING)
            status_text.text("💾 Salvando post...")
            progress_bar.progress(95)

            text_data = {
                "theme": user_topic,
                "platform": platform if platform else "GENERIC",
                "content": generated_text,
                "is_approved": False
            }

            # Registrar na API do projeto unipost-api
            try:
                send_result = TextsRequest().create_text(
                    token=token,
                    text_data=text_data
                )
                logger.info(
                    f"Text successfully registered in API: {send_result}")

                # Armazenar o ID do texto para usar nos botões de aprovação
                created_text_id = send_result.get("text_id")

            except Exception as api_error:
                logger.error(f"Error registering in API: {api_error}")
                send_result = {
                    "success": False,
                    "message": f"""❌ **Erro ao registrar na API**: {
                        str(api_error)
                    }""",
                    "text_id": None
                }
                created_text_id = None

            progress_bar.progress(100)
            status_text.text("✅ Post salvo")

            # Processamento concluído

            # Limpar barra de progresso antes de mostrar resultado
            progress_bar.empty()
            status_text.empty()

            # Exibir resultado na área direita
            with result_container.container():
                st.toast("Post Gerado com Sucesso!", icon="✅")

                # Informações dos parâmetros
                platform_name = (PLATFORMS.get(platform, 'Genérico')
                                 if platform else 'Genérico')

                # Contar palavras do post gerado
                word_count = len(
                    generated_text.split()
                ) if generated_text else 0
                target_count = self.text_service.extract_word_count(length)

                # Mostrar informações em formato nativo
                st.info(f"""
                📱 **Plataforma:** {platform_name}
                📝 **Tom:** {tone.title()}
                🎨 **Criatividade:** {creativity_level.title()}
                📏 **Tamanho:** {length}
                📚 **Referências:** {len(similar_texts)}
                📊 **Palavras:** {word_count} (alvo: {target_count})
                """)

                # Post gerado principal
                with st.container():
                    st.markdown("**📄 Post Gerado:**")
                    st.markdown(generated_text)

                # Seção de ações
                st.subheader("🎛️ Ações Disponíveis")

                col_approve, col_reject, col_regenerate = st.columns(3)

                # Botão Aprovar - Gerar embedding quando aprovado
                with col_approve:
                    if st.button(
                        "✅ Aprovar Post",
                        key="approve_generated",
                        use_container_width=True,
                        type="primary",
                        help="Aprovar post"
                    ):
                        # Aprovar post e gerar embedding
                        if created_text_id:
                            with st.spinner(
                                "Aprovando post..."
                            ):
                                approval_result = TextsRequest().approve_and_generate_embedding(  # noqa: E501
                                    token,
                                    created_text_id,
                                    generated_text,
                                    user_topic
                                )
                            st.toast(approval_result, icon="✅")

                            if 'last_generated' in st.session_state:
                                st.session_state[
                                    'last_generated'
                                ]['approved'] = True
                            st.rerun()
                        else:
                            st.toast(
                                "Erro: ID do texto não encontrado",
                                icon="❌"
                            )

                # Botão Reprovar
                with col_reject:
                    if st.button(
                        "❌ Reprovar",
                        key="reject_generated",
                        use_container_width=True,
                        type="secondary",
                        help="Reprovar post"
                    ):
                        # Reprovar post
                        if created_text_id:
                            with st.spinner("Reprovando post..."):
                                rejection_result = TextsRequest().reject_text(
                                    token, created_text_id
                                )
                            st.toast(rejection_result, icon="❌")

                            if 'last_generated' in st.session_state:
                                st.session_state[
                                    'last_generated'
                                ]['approved'] = False
                            st.rerun()
                        else:
                            st.toast(
                                "Erro: ID do texto não encontrado",
                                icon="❌"
                            )

                # Botão Regenerar (sempre ativo)
                with col_regenerate:
                    if st.button(
                        "🔄 Regenerar",
                        key="regenerate_generated",
                        use_container_width=True,
                        type="secondary",
                        help="Regenerar post"
                    ):
                        # Preparar dados para regeneração
                        if 'last_generated' in st.session_state:
                            last_data = st.session_state['last_generated']
                            st.session_state.regenerate_text_data = {
                                'theme': last_data.get('theme', ''),
                                'platform': platform,
                                'tone': tone,
                                'creativity': creativity_level,
                                'length': length
                            }
                            del st.session_state['last_generated']

                        st.toast("Regenerando post...", icon="🔄")
                        st.rerun()

                # Mostrar resultado do registro na API
                if send_result.get("success"):
                    import time
                    st.toast("✅ Texto gerado com sucesso", icon="✅")
                    time.sleep(2.5)
                else:
                    st.error(
                        f"""🚨 Erro no registro: {
                            send_result.get('message', 'Erro desconhecido')
                        }"""
                    )

                # Salvar na sessão com ID do post criado
                st.session_state['last_generated'] = {
                    'text': generated_text,
                    'platform': platform_name,
                    'tone': tone,
                    'creativity': creativity_level,
                    'length': length,
                    'text_data': text_data,  # Dados enviados para API
                    'approved': False,  # Texto criado sem aprovação inicial
                    'theme': user_topic
                }

        except Exception as e:
            st.toast(f"Erro durante o processamento: {e}", icon="❌")
            logger.error(f"Error in text generation process: {e}")

        finally:
            # Garantir limpeza dos elementos de progresso
            try:
                progress_bar.empty()
                status_text.empty()
            except Exception:
                pass  # Elementos podem já ter sido removidos

    def create(self, token, menu_position, permissions):
        # menu_position não utilizado nesta função
        _ = menu_position
        """
        Gera um novo post usando IA.

        Parameters
        ----------
        token : str
            O token obtido e passado para a validação da requisição.
        menu_position : Any
            A posição do menu superior.
        permissions : list
            A lista de permissões do usuário.
        """
        # Limpar dados de post anterior ao acessar a tela
        if 'last_generated' in st.session_state:
            del st.session_state['last_generated']

        # Exibir status dos serviços no menu
        if 'create' in permissions:

            # Layout principal: Parâmetros | Resultado
            # Novos campos obrigatórios
            col_params, col_result = st.columns([1.0, 1.2])

            with col_params:
                # Cabeçalho da seção de parâmetros
                st.header("🎨 Parâmetros de Geração")

                # Verificar se há dados de regeneração salvos
                regenerate_data = st.session_state.get(
                    'regenerate_text_data',
                    {}
                )
                default_theme = regenerate_data.get('theme', '')

                # Mostrar aviso se for regeneração
                if regenerate_data:
                    st.info(
                        "🔄 **Modo Regeneração**: Tema carregado " +
                        "automaticamente do post selecionado."
                    )

                # Título para o campo tema
                st.markdown("**🎯 Tema do post**")
                st.caption("Seja específico, use palavras-chave relevantes")

                text_topic = st.text_area(
                    label="",
                    value=default_theme,
                    max_chars=500,
                    placeholder="Ex: Benefícios da energia renovável",
                    help="Tema para o post",
                    height=120,
                    key="topic_input",
                    label_visibility="collapsed"
                )

                # Organizar campos lado a lado
                col_plat, col_tone = st.columns(2)

                with col_plat:
                    # Seleção de plataforma
                    platform_options = list(PLATFORMS.keys())
                    platform_display = {
                        k: f"{v}" for k,
                        v in PLATFORMS.items()}

                    selected_platform = st.selectbox(
                        "📱 Plataforma de destino",
                        platform_options,
                        format_func=(
                            lambda x: platform_display.get(x, x)
                        ),  # type: ignore
                        help="Plataforma de destino",
                        key="platform_input"
                    )  # type: ignore

                with col_tone:
                    # Tom da linguagem (otimizado sem duplicações)
                    tone_options = [
                        "informal",
                        "formal",
                        "educativo",
                        "técnico",
                        "inspiracional"
                    ]
                    selected_tone = st.selectbox(
                        "📝 Tom da linguagem",
                        tone_options,
                        index=0,
                        help="Tom do conteúdo",
                        key="tone_input")

                # Segunda linha de campos emparelhados
                col_length, col_creativity = st.columns(2)

                with col_length:
                    selected_word_count = st.slider(
                        "📏 Quantidade de palavras",
                        min_value=50,
                        max_value=800,
                        value=300,
                        step=25,
                        help="Número de palavras",
                        key="word_count_input"
                    )
                    # Converter para formato esperado pelo backend
                    selected_length = f"Exato ({selected_word_count} palavras)"

                with col_creativity:
                    selected_creativity = st.selectbox(
                        "🎨 Nível de criatividade",
                        [
                            "conservador",
                            "equilibrado",
                            "criativo",
                            "inovador"
                        ],
                        index=1,
                        help="Nível de criatividade",
                        key="creativity_input")

                # Terceira linha de configurações adicionais
                col_hashtags, col_cta = st.columns(2)

                with col_hashtags:
                    include_hashtags = st.checkbox(
                        "#️⃣ Incluir hashtags",
                        value=True,
                        help="Incluir hashtags"
                    )

                with col_cta:
                    include_cta = st.checkbox(
                        "📢 Incluir call-to-action",
                        value=False,
                        help="Incluir CTA"
                    )

                # Botão de geração
                generate_button = st.button(
                    "🚀 Gerar Post com IA",
                    use_container_width=True,
                    type="primary",
                    key="generate_btn",
                    help="Gerar post"
                )

            # Área de resultado
            with col_result:
                # Cabeçalho da seção de resultado
                st.header("📄 Resultado da Geração")

                result_container = st.container()

                # Estado inicial limpo
                if not generate_button:
                    with result_container:
                        st.info("""
                        🤖 **Aguardando Geração**

                        Configure os parâmetros e clique em **"🚀 Gerar Post"**.
                        """)

            # Processar geração se botão foi clicado
            if generate_button:
                # Marcar como gerando
                st.session_state.generating = True

                # Validação com feedback visual melhorado
                if not text_topic or not text_topic.strip():
                    st.session_state.generating = False
                    st.error("Preencha o tema do post")
                elif len(text_topic.strip()) < 5:
                    st.session_state.generating = False
                    st.warning("Tema muito curto (mín. 5 caracteres)")
                elif len(text_topic.strip()) > 500:
                    st.session_state.generating = False
                    st.error("Tema muito longo (máx. 500 caracteres)")
                else:
                    # Validação passou - processar geração
                    query = text_topic.strip()
                    platform_code = selected_platform if (
                        selected_platform != "GENERIC"
                    ) else ""

                    try:
                        self._process_text_generation_improved(
                            text_topic.strip(),
                            query,
                            platform_code,
                            selected_tone,
                            selected_creativity,
                            selected_length,
                            include_hashtags,
                            include_cta,
                            token,
                            result_container
                        )
                    finally:
                        # Sempre limpar o estado de geração
                        st.session_state.generating = False

        elif 'create' not in permissions:
            st.warning("""
            **🔒 Acesso Restrito**

            Sem permissão para gerar posts.
            """)

    def render(self, token, menu_position, permissions):
        # menu_position não utilizado nesta função
        _ = menu_position
        """
        Interface para renderização dos posts gerados.

        Parameters
        ----------
        token : str
            O token utilizado no envio da requisição.
        menu_position : Any
            posição do menu superior com a listagem dos posts.
        permissions : list
            Lista contendo as permissões do usuário.
        """
        if 'read' in permissions:

            texts = TextsRequest().get_texts(token)

            if not texts:
                st.empty()
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.info("""
                    **📄 Biblioteca Vazia**

                    Nenhum post foi encontrado. Que tal criar seu primeiro post?

                    👉 Vá para **"🚀 Gerar Novo Post"** no menu acima.
                    """)
                return

            # Cabeçalho da biblioteca
            st.header("📚 Biblioteca de Posts")
            st.caption("Gerencie e visualize todos os posts criados com IA")

            # Barra de filtros melhorada
            col_filter1, col_filter2, col_filter3, col_filter4 = st.columns([3, 2, 2, 1])

            with col_filter1:
                search_text = st.text_input(
                    "🔍 Buscar por tema ou conteúdo",
                    placeholder="Digite palavras-chave para buscar...",
                    help="Busque por tema ou conteúdo do post"
                )

            with col_filter2:
                status_filter = st.selectbox(
                    "📊 Filtrar por Status",
                    ["Todos", "✅ Aprovados", "⏳ Pendentes"],
                    index=0,
                    help="Filtrar posts por status de aprovação"
                )

            with col_filter3:
                sort_options = ["📅 Mais Recentes", "📅 Mais Antigos", "📝 Mais Palavras", "📝 Menos Palavras"]
                sort_option = st.selectbox(
                    "🔄 Ordenar por",
                    sort_options,
                    index=0,
                    help="Escolha como ordenar os posts"
                )

            with col_filter4:
                posts_per_page = st.selectbox(
                    "📄 Por página",
                    [5, 10, 20, 50],
                    index=1,
                    help="Quantidade de posts por página"
                )

            # Aplicar filtros
            filtered_texts = texts
            if status_filter == "✅ Aprovados":
                filtered_texts = [t for t in filtered_texts if t.get('is_approved', False)]
            elif status_filter == "⏳ Pendentes":
                filtered_texts = [t for t in filtered_texts if not t.get('is_approved', False)]

            if search_text:
                search_lower = search_text.lower()
                filtered_texts = [
                    t for t in filtered_texts
                    if search_lower in t.get('theme', '').lower() or
                       search_lower in t.get('content', t.get('generated_text', '')).lower()
                ]

            # Aplicar ordenação
            if sort_option == "📅 Mais Antigos":
                filtered_texts.sort(key=lambda x: x.get('created_at', ''), reverse=False)
            elif sort_option == "📝 Mais Palavras":
                filtered_texts.sort(key=lambda x: len(x.get('content', x.get('generated_text', '')).split()), reverse=True)
            elif sort_option == "📝 Menos Palavras":
                filtered_texts.sort(key=lambda x: len(x.get('content', x.get('generated_text', '')).split()), reverse=False)
            else:  # Mais recentes (padrão)
                filtered_texts.sort(key=lambda x: x.get('created_at', ''), reverse=True)

            if not filtered_texts:
                st.info("🔍 Nenhum post encontrado com os filtros aplicados")
                return

            # Estatísticas resumidas
            total_approved = len([t for t in filtered_texts if t.get('is_approved', False)])
            total_pending = len(filtered_texts) - total_approved

            col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
            with col_stats1:
                st.metric("📄 Total Encontrados", len(filtered_texts))
            with col_stats2:
                st.metric("✅ Aprovados", total_approved)
            with col_stats3:
                st.metric("⏳ Pendentes", total_pending)
            with col_stats4:
                approval_rate = (total_approved / len(filtered_texts) * 100) if filtered_texts else 0
                st.metric("📊 Taxa Aprovação", f"{approval_rate:.0f}%")

            st.divider()

            # Paginação
            total_posts = len(filtered_texts)
            total_pages = (total_posts - 1) // posts_per_page + 1 if total_posts > 0 else 1

            if total_pages > 1:
                col_pagination1, col_pagination2, col_pagination3 = st.columns([1, 2, 1])
                with col_pagination2:
                    current_page = st.selectbox(
                        f"📄 Página ({total_pages} páginas)",
                        range(1, total_pages + 1),
                        index=0,
                        format_func=lambda x: f"Página {x} de {total_pages}"
                    )
            else:
                current_page = 1

            # Calcular posts da página atual
            start_idx = (current_page - 1) * posts_per_page
            end_idx = start_idx + posts_per_page
            posts_to_show = filtered_texts[start_idx:end_idx]

            # Exibir posts com design melhorado
            for i, text in enumerate(posts_to_show):
                is_approved = text.get('is_approved', False)
                status_emoji = '✅' if is_approved else '⏳'
                status_color = 'success' if is_approved else 'warning'

                # Formatação da data melhorada
                created_date = text.get('created_at', 'N/A')
                if created_date != 'N/A' and len(created_date) >= 10:
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(created_date[:10], '%Y-%m-%d')
                        formatted_date = date_obj.strftime('%d/%m/%Y')
                        time_part = created_date[11:16] if len(created_date) > 16 else ''
                        full_date = f"{formatted_date} {time_part}".strip()
                    except Exception:
                        full_date = created_date[:16] if len(created_date) >= 16 else created_date
                else:
                    full_date = 'Data não disponível'

                theme_display = text.get('theme', 'Sem título')
                content_text = text.get('content', text.get('generated_text', ''))
                word_count = len(content_text.split()) if content_text else 0
                char_count = len(content_text) if content_text else 0
                platform_name = PLATFORMS.get(text.get('platform', 'N/A'), 'Genérico')

                # Preview do conteúdo (primeiras 150 caracteres)
                content_preview = content_text[:150] + "..." if len(content_text) > 150 else content_text

                # Container principal do post com design de card
                text_id = text.get('id')

                # Usar container com borda
                with st.container():
                    # Cabeçalho do card
                    col_header, col_status = st.columns([4, 1])

                    with col_header:
                        st.markdown(f"### {status_emoji} {theme_display}")

                    with col_status:
                        if is_approved:
                            st.success("Aprovado")
                        else:
                            st.warning("Pendente")

                    # Informações do post
                    col_info1, col_info2, col_info3, col_info4 = st.columns(4)

                    with col_info1:
                        st.metric("📅 Data", full_date[:10])

                    with col_info2:
                        st.metric("📱 Plataforma", platform_name)

                    with col_info3:
                        st.metric("📝 Palavras", word_count)

                    with col_info4:
                        st.metric("📊 Caracteres", char_count)

                    # Preview do conteúdo
                    st.markdown("**📄 Preview do Conteúdo:**")
                    st.markdown(f"*{content_preview}*")

                    # Layout de ações
                    col_text, col_actions = st.columns([3, 1])

                    # Coluna esquerda: visualização completa do texto
                    with col_text:
                        with st.expander("👁️ Ver Texto Completo", expanded=False):
                            st.text_area(
                                "Conteúdo completo do post:",
                                value=content_text,
                                height=250,
                                label_visibility="collapsed",
                                key=f"post_text_{text_id}_{i}_{current_page}"
                            )

                    # Coluna direita: botões de ação
                    with col_actions:
                        st.markdown("**🎛️ Ações:**")

                        if not is_approved and 'update' in permissions:
                            if st.button(
                                "✅ Aprovar",
                                key=f"approve_{text_id}_{i}_{current_page}",
                                help="Aprovar este post",
                                use_container_width=True,
                                type="primary"
                            ):
                                with st.spinner("Aprovando post..."):
                                    text_content = text.get('content', '')
                                    text_theme = text.get('theme', '')
                                    result = TextsRequest().approve_and_generate_embedding(
                                        token, text_id, text_content, text_theme
                                    )
                                st.toast(result, icon="✅")
                                st.rerun()

                        elif is_approved and 'update' in permissions:
                            if st.button(
                                "❌ Reprovar",
                                key=f"reject_{text_id}_{i}_{current_page}",
                                help="Reprovar este post",
                                use_container_width=True,
                                type="secondary"
                            ):
                                with st.spinner("Reprovando post..."):
                                    result = TextsRequest().reject_text(token, text_id)
                                st.toast(result, icon="❌")
                                st.rerun()

                        if 'create' in permissions:
                            if st.button(
                                "🔄 Regenerar",
                                key=f"regenerate_{text_id}_{i}_{current_page}",
                                help="Regenerar post baseado neste tema",
                                use_container_width=True,
                                type="secondary"
                            ):
                                st.session_state.regenerate_text_data = {
                                    'theme': text.get('theme', ''),
                                    'original_id': text_id
                                }
                                st.toast("Tema carregado para regeneração!", icon="🔄")
                                st.switch_page("🚀 Gerar Novo Post")

                    st.divider()

            # Navegação de páginas no final
            if total_pages > 1:
                col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
                with col_nav2:
                    st.info(f"📄 Mostrando posts {start_idx + 1} a {min(end_idx, total_posts)} de {total_posts}")

        elif 'read' not in permissions:
            st.error("""
            **🔒 Acesso Restrito**

            Você não possui permissão para visualizar posts.
            Entre em contato com o administrador para solicitar acesso.
            """)

    def update(self, token, menu_position, permissions):
        """
        Menu com interface para atualização do post.

        Parameters
        ----------
        token : str
            O token utilizado no envio da requisição.
        menu_position : Any
            posição do menu superior com a listagem dos posts.
        permissions : list
            Lista contendo as permissões do usuário.
        """

        if 'update' in permissions:
            texts = TextsRequest().get_texts(token)

            if not texts:
                _, col5, _ = st.columns(3)
                with col5:
                    st.info("""
                    **📄 Nenhum post encontrado**

                    Não há posts para edição.
                    """)
                return

            # Seleção do post no menu superior
            with menu_position:
                st.markdown("### 🎯 Selecionar Post")
                texts_options = {}
                for text in texts:
                    theme_preview = text['theme'][:50]
                    theme_preview += '...' if len(text['theme']) > 50 else ''
                    status = ('Aprovado' if text.get('is_approved')
                              else 'Pendente')
                    key = f"{theme_preview} ({status})"
                    texts_options[key] = text['id']

                selected_text_display = st.selectbox(
                    "Escolha o post para editar:",
                    options=list(texts_options.keys()),
                    help="Selecione um post"
                )
                selected_text_id = texts_options[selected_text_display]

            # Interface de edição
            text_data = TextsRequest().get_text(token, selected_text_id)

            if text_data:
                col_form, col_preview = st.columns([1, 1])

                with col_form:
                    st.subheader("📝 Dados do Post")

                    new_topic = st.text_area(
                        label="🎯 Tema",
                        value=text_data['theme'],
                        max_chars=500,
                        help="Tema do post",
                        height=100
                    )

                    status_options = {
                        True: "✅ Aprovado",
                        False: "⏳ Pendente"
                    }

                    current_approval_status = text_data.get(
                        'is_approved', False)

                    new_status_display = st.selectbox(
                        label="📊 Status",
                        options=list(status_options.values()),
                        index=0 if current_approval_status else 1,
                        help="Status do post"
                    )

                    # Converter de volta para o valor da API
                    new_approval_status = new_status_display == "✅ Aprovado"

                with col_preview:

                    st.subheader("👁️ Prévia das Alterações")

                    # Verificar se houve mudanças
                    has_changes = (
                        new_topic != text_data['theme'] or
                        new_approval_status != text_data.get('is_approved'))

                    if has_changes:
                        st.toast("Alterações detectadas!", icon="📝")
                    else:
                        st.toast("Nenhuma alteração feita", icon="ℹ️")

                    if new_topic:
                        topic_preview = (new_topic[:200]
                                         if len(new_topic) > 200
                                         else new_topic)
                        topic_suffix = '...' if len(new_topic) > 200 else ''
                        st.markdown(f"""
                        **🎯 Novo Tema:**
                        {topic_preview}{topic_suffix}

                        **📊 Novo Status:**
                        {status_options[new_approval_status]}

                        **📅 Data Original:**
                        {text_data.get('created_at', 'N/A')[:10]}

                        **📊 Caracteres:** {len(new_topic)}/500""")

                # Validação e botão de atualização
                if new_topic:
                    validated_topic, topic_data = self.validate_topic(
                        new_topic)

                    if validated_topic and has_changes:
                        _, col_btn2, _ = st.columns([1, 2, 1])

                        with col_btn2:
                            confirm_button = st.button(
                                "💾 Salvar Alterações",
                                use_container_width=True,
                                type="primary",
                                help="Salvar alterações"
                            )

                            if confirm_button:
                                new_text_data = {
                                    "theme": topic_data,
                                    "is_approved": new_approval_status
                                }

                                with st.spinner("Salvando alterações..."):
                                    returned_text = TextsRequest().update_text(
                                        token=token,
                                        text_id=text_data['id'],
                                        updated_data=new_text_data
                                    )

                                st.toast(
                                    "Post atualizado com sucesso!",
                                    icon="✅"
                                )
                                st.balloons()
                                st.toast(returned_text, icon="ℹ️")
                                st.rerun()

                # Área de prévia do post completo
                with st.expander(
                    "📄 Visualizar Post Completo",
                    expanded=False
                ):
                    content_text = text_data.get(
                        'content', text_data.get(
                            'generated_text', 'Post não disponível'))

                    st.text_area(
                        "Conteúdo completo do post:",
                        value=content_text,
                        height=400,
                        label_visibility="collapsed"
                    )

        elif 'update' not in permissions:
            st.warning("""
            **🔒 Acesso Restrito**

            Sem permissão para atualizar posts.
            """)

    def main_menu(self, token, permissions):
        """
        Menu principal da aplicação de geração de posts.

        Parameters
        ----------
        token : str
            Token utilizado para as requisições.
        permissions : str
            Lista com as permissões do usuário.
        """
        class_permissions = TextsRequest().get_text_permissions(
            user_permissions=permissions
        )

        # Cabeçalho principal mais limpo
        _, col_menu, col_actions = st.columns([1, 1.2, 1])

        with col_menu:
            # Menu com ícones mais intuitivos
            menu_options = {
                "📚 Biblioteca de Posts": self.render,
                "🚀 Gerar Novo Post": self.create,
            }

            # Verificar permissões e filtrar opções disponíveis
            available_options = {}
            if 'read' in class_permissions:
                available_options["📚 Biblioteca de Posts"] = (
                    menu_options["📚 Biblioteca de Posts"]
                )
            if 'create' in class_permissions:
                available_options["🚀 Gerar Novo Post"] = (
                    menu_options["🚀 Gerar Novo Post"]
                )

            if available_options:
                selected_option = st.selectbox(
                    label="Escolha uma ação:",
                    options=list(available_options.keys()),
                    help="Selecione uma opção",
                    label_visibility="collapsed"
                )
            else:
                st.toast(
                    "Você não possui permissões para usar esta funcionalidade",
                    icon="❌")
                return

        # Mostrar informações de permissão
        with col_actions:
            permission_status = []
            if 'read' in class_permissions:
                permission_status.append("👁️ Visualizar")
            if 'create' in class_permissions:
                permission_status.append("➕ Criar")

        st.divider()

        # Executar a opção selecionada
        if available_options:
            executed_option = available_options[selected_option]
            executed_option(
                token=token,
                menu_position=col_actions,
                permissions=class_permissions
            )
