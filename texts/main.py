import streamlit as st
import pandas as pd
from texts.request import TextsRequest
from dictionary.vars import PLATFORMS
from time import sleep
from services.elasticsearch_service import ElasticsearchService
from services.redis_service import RedisService
from services.text_generation_service import TextGenerationService
import logging

logger = logging.getLogger(__name__)


class Texts:
    """
    Classe que representa os métodos referentes à geração de post natural.
    Implementa o fluxo completo conforme roadmap:
    - Busca automática de posts no ElasticSearch
    - Vetorização usando SentenceTransformers
    - Cache dos vetores no Redis
    - Interface para input do usuário
    - Elaboração de conpost de prompt
    - Geração de post via LLM e webhook
    """

    def __init__(self):
        self.es_service = ElasticsearchService()
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

        df = df.sort_values(by="Data de Criação", ascending=False)

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
        """
        # Criar interface de progresso na área de resultado
        with result_container.container():
            st.markdown("""
            <div style="text-align: center; margin-bottom: 20px;">
                <h3 style="color: #1f77b4;">🚀 Gerando Post com IA</h3>
                <p style="color: #666;">
                    Processando sua solicitação...
                </p>
            </div>
            """, unsafe_allow_html=True)

            progress_bar = st.progress(0)
            status_text = st.empty()

        try:
            # 1. Verificar cache Redis
            status_text.text("🔍 Verificando cache Redis...")
            progress_bar.progress(10)

            cached_data = self.redis_service.get_cached_vectors(search_query)

            if cached_data:
                vectors = cached_data['vectors']
                texts = cached_data['texts']
                status_text.text("✅ Dados encontrados no cache")
            else:
                # 2. Busca automática no ElasticSearch
                status_text.text("🔍 Buscando posts no ElasticSearch...")
                progress_bar.progress(20)

                raw_texts = self.es_service.search_texts(search_query)

                # Permite geração mesmo sem resultados do ElasticSearch
                if raw_texts:
                    # 3. Tratamento dos posts
                    status_text.text("⚙️ Tratando posts encontrados...")
                    progress_bar.progress(40)

                    texts = self.text_service.treat_text_content(raw_texts)

                    if texts:
                        # 4. Vetorização usando SentenceTransformers
                        status_text.text("🧠 Gerando vetores semânticos...")
                        progress_bar.progress(60)

                        vectors = self.text_service.vectorize_texts(texts)

                        if vectors:
                            # 5. Cache no Redis
                            self.redis_service.cache_vectors(
                                search_query, vectors, texts)
                        else:
                            st.toast(
                                """Erro na vetorização,
                                prosseguindo sem referências""",
                                icon="⚠️")
                            sleep(2)
                            vectors, texts = [], []
                    else:
                        st.toast(
                            """Posts inválidos após tratamento,
                            prosseguindo sem referências""",
                            icon="⚠️")
                        sleep(2)
                        vectors, texts = [], []
                else:
                    st.toast(
                        """Nenhuma referência encontrada no ElasticSearch,
                        gerando baseado apenas no tema""",
                        icon="ℹ️")
                    sleep(2)
                    vectors, texts = [], []

            # 6. Busca de vetores similares ao tema (se disponível)
            similar_texts = []
            if vectors and texts:
                status_text.text("🎯 Encontrando posts similares...")
                progress_bar.progress(70)

                similar_texts = self.text_service.find_similar_vectors(
                    user_topic, vectors, texts)
                if not similar_texts:
                    st.toast(
                        "Nenhuma referência similar encontrada",
                        icon="ℹ️"
                    )
                    sleep(2)

            # 7. Elaboração do contexto de prompt com novos parâmetros
            status_text.text("📝 Criando contexto do prompt...")
            progress_bar.progress(80)

            prompt_context = self.text_service.create_prompt_context(
                user_topic,
                similar_texts,
                platform,
                tone,
                creativity_level,
                length
            )

            # 8. Geração de post via OpenAI/LLM
            status_text.text("🤖 Gerando post com IA...")
            progress_bar.progress(90)

            generated_text = self.text_service.generate_text_via_llm(
                prompt_context
            )
            if not generated_text:
                st.toast("Erro na geração de post via IA", icon="❌")
                sleep(2)
                return

            # 9. Envio para aprovação via webhook
            status_text.text("📤 Enviando para aprovação...")
            progress_bar.progress(95)

            approval_sent = self.text_service.send_for_approval(
                generated_text, user_topic)

            # 10. Salvar no banco de dados da API UniPost
            text_data = {
                "theme": user_topic,
                "platform": platform if platform else "GENERIC",
                "content": generated_text,
                "is_approved": False  # Sempre False inicialmente
            }

            # Registrar na API do projeto unipost-api
            try:
                send_result = TextsRequest().create_text(
                    token=token,
                    text_data=text_data
                )
                logger.info(
                    f"Text successfully registered in API: {send_result}")
            except Exception as api_error:
                logger.error(f"Error registering in API: {api_error}")
                send_result = "Erro ao registrar na API"

            progress_bar.progress(100)
            status_text.text("✅ Processo concluído com sucesso!")

            # Pequena pausa para mostrar conclusão
            import time
            time.sleep(0.5)

            # Limpar barra de progresso antes de mostrar resultado
            progress_bar.empty()
            status_text.empty()

            # Exibir resultado na área direita
            with result_container.container():
                st.toast("Post Gerado com Sucesso!", icon="✅")
                sleep(2)

                # Informações dos parâmetros
                platform_name = (PLATFORMS.get(platform, 'Genérico')
                                 if platform else 'Genérico')

                # Contar palavras do post gerado
                word_count = len(
                    generated_text.split()
                ) if generated_text else 0
                target_count = self.text_service.extract_word_count(length)

                # Cor baseada na precisão da contagem
                count_color = "#28a745" if abs(
                    word_count - target_count
                ) <= 20 else "#ffc107"

                st.markdown(f"""
                <div style="
                    background: #e7f3ff;
                    padding: 10px;
                    border-radius: 6px;
                    margin-bottom: 15px;
                    font-size: 12px;
                    border-left: 3px solid #007bff;
                ">
                    📱 {platform_name} • 📝 {tone.title()} •
                    🎨 {creativity_level.title()} • 📏 {length}
                    <br>📚 {len(similar_texts)} referências •
                    <span style="color: {count_color}; font-weight: bold;">
                        📊 {word_count} palavras (alvo: {target_count})
                    </span>
                </div>
                """, unsafe_allow_html=True)

                # Post gerado principal
                formatted_text = generated_text.replace('\n', '<br>')
                st.markdown(f"""
                <div style="
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    border: 1px solid #e9ecef;
                    margin-bottom: 15px;
                    line-height: 1.6;
                    font-size: 15px;
                ">
                {formatted_text}
                </div>
                """, unsafe_allow_html=True)

                # Botões de ação (mesmo padrão da lista)
                st.markdown("**🎛️ Ações:**")
                col_approve, col_reject, col_regenerate = st.columns(3)

                # Botão Aprovar/Aprovado
                with col_approve:
                    approve_disabled = approval_sent
                    if st.button(
                        "✅ Aprovar" if not approval_sent else "✅ Aprovado",
                        key="approve_generated",
                        use_container_width=True,
                        type="secondary" if not approve_disabled else (
                            "primary"
                        ),
                        disabled=approve_disabled,
                        help="Marcar como aprovado" if not approve_disabled
                        else "Já foi para aprovação"
                    ):
                        # Simular aprovação (post já foi registrado na API)
                        st.toast("Status atualizado para aprovado!", icon="✅")
                        if 'last_generated' in st.session_state:
                            st.session_state[
                                'last_generated'
                            ]['approved'] = True
                        sleep(2)
                        st.rerun()

                # Botão Reprovar/Reprovado
                with col_reject:
                    reject_disabled = not approval_sent
                    if st.button(
                        "❌ Reprovar" if approval_sent else "❌ Reprovado",
                        key="reject_generated",
                        use_container_width=True,
                        type="secondary" if not reject_disabled else "primary",
                        disabled=reject_disabled,
                        help="Marcar como reprovado" if not reject_disabled
                        else "Ainda não foi aprovado"
                    ):
                        st.toast("Status atualizado para reprovado!", icon="❌")
                        if 'last_generated' in st.session_state:
                            st.session_state[
                                'last_generated'
                            ]['approved'] = False
                        sleep(2)
                        st.rerun()

                # Botão Regenerar (sempre ativo)
                with col_regenerate:
                    if st.button(
                        "🔄 Regenerar",
                        key="regenerate_generated",
                        use_container_width=True,
                        type="secondary",
                        help="Gerar novo post com os mesmos parâmetros"
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

                        st.toast(
                            "Regenerando post com os mesmos parâmetros...",
                            icon="🔄"
                        )
                        sleep(2)
                        st.rerun()

                # Referências compactas
                if similar_texts:
                    with st.expander(f"📖 Referências ({len(similar_texts)})"):
                        for i, (text, score) in enumerate(
                                similar_texts[:3], 1):
                            st.caption(
                                f"**{i}.** ({score:.2f}) {text[:150]}...")

                st.toast(f"✅ {send_result}")

                # Salvar na sessão com ID do post criado
                st.session_state['last_generated'] = {
                    'text': generated_text,
                    'platform': platform_name,
                    'tone': tone,
                    'creativity': creativity_level,
                    'length': length,
                    'text_data': text_data,  # Dados enviados para API
                    'approved': approval_sent,
                    'theme': user_topic
                }

        except Exception as e:
            st.toast(f"Erro durante o processamento: {e}", icon="❌")
            logger.error(f"Error in text generation process: {e}")
            sleep(2)

        finally:
            # Garantir limpeza dos elementos de progresso
            try:
                progress_bar.empty()
                status_text.empty()
            except Exception:
                pass  # Elementos podem já ter sido removidos

    def create(self, token, menu_position, permissions):
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
        # Exibir status dos serviços no menu
        if 'create' in permissions:

            # Layout principal: Parâmetros | Resultado
            # Novos campos obrigatórios
            col_params, col_result = st.columns([1.0, 1.2])

            with col_params:
                st.subheader("🎨 Parâmetros de Geração")

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

                text_topic = st.text_area(
                    label="🎯 Tema do post",
                    value=default_theme,
                    max_chars=500,
                    placeholder="Ex: Benefícios da energia renovável" +
                    " para o meio ambiente",
                    help="Descreva detalhadamente o tema que deseja abordar.",
                    height=120,
                    key="topic_input")

                search_query = st.text_input(
                    label="🔍 Consulta de busca (opcional)",
                    placeholder="Ex: energia solar, sustentabilidade," +
                    " meio ambiente",
                    help="Termos específicos para busca no banco de dados." +
                    " Se não fornecido, usará o tema como consulta",
                    key="search_input")

                # Organizar campos lado a lado
                col_plat, col_tone = st.columns(2)

                with col_plat:
                    # Seleção de plataforma
                    platform_options = list(PLATFORMS.keys())
                    platform_display = {
                        k: f"{v}" for k,
                        v in PLATFORMS.items()}
                    platform_display["GENERIC"] = (
                        "Genérico (sem plataforma específica)"
                    )
                    platform_options.insert(0, "GENERIC")

                    selected_platform = st.selectbox(
                        "📱 Plataforma de destino",
                        platform_options,
                        format_func=(
                            lambda x: platform_display.get(x, x)
                        ),  # type: ignore
                        help="Selecione a plataforma onde" +
                        " o conteúdo será publicado",
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
                        help="Defina o tom que melhor se " +
                        "adequa ao seu público",
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
                        help="Defina exatamente quantas palavras o post terá",
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
                        help="Controle o nível de criatividade e " +
                        "originalidade do post",
                        key="creativity_input")

                # Terceira linha de configurações adicionais
                col_hashtags, col_cta = st.columns(2)

                with col_hashtags:
                    include_hashtags = st.checkbox(
                        "#️⃣ Incluir hashtags",
                        value=True,
                        help="Adicionar hashtags relevantes ao conteúdo"
                    )

                with col_cta:
                    include_cta = st.checkbox(
                        "📢 Incluir call-to-action",
                        value=False,
                        help="Adicionar chamada para ação no final do post"
                    )

                # Botão de gerar sempre visível
                st.markdown("<br>", unsafe_allow_html=True)
                generate_button = st.button(
                    "🚀 Gerar Post",
                    use_container_width=True,
                    type="primary",
                    key="generate_btn",
                    help="Clique para gerar o post com os parâmetros")

            # Área de resultado
            with col_result:
                result_container = st.container()

                # Estado inicial
                if not generate_button and 'last_generated' not in (
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
                            <h3 style="color: #6c757d;">📄 Resultado</h3>
                            <p style="color: #6c757d;">
                                O post gerado aparecerá aqui
                            </p>
                            <div style="margin-top: 20px; font-size: 48px;">
                                🤖
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # Exibir último resultado se existe
                elif 'last_generated' in st.session_state:
                    last_data = st.session_state['last_generated']
                    with result_container:
                        st.toast("Post anterior carregado", icon="📄")
                        sleep(1)

                        # Mostrar informações do post anterior
                        st.markdown(f"""
                        <div style="
                            background: #e7f3ff;
                            padding: 10px;
                            border-radius: 6px;
                            margin-bottom: 15px;
                            font-size: 12px;
                            border-left: 3px solid #007bff;
                        ">
                            📱 {last_data.get('platform', 'N/A')} • 📝 {
                                last_data.get('tone', 'N/A').title()} •
                            🎨 {last_data.get(
                                    'creativity', 'N/A'
                                ).title()} • 📏 {last_data.get('length', 'N/A')}
                        </div>
                        """, unsafe_allow_html=True)

                        # Mostrar texto anterior
                        formatted_text = last_data.get('text', '').replace(
                            '\n', '<br>'
                        )
                        st.markdown(f"""
                        <div style="
                            background: white;
                            padding: 20px;
                            border-radius: 10px;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            border: 1px solid #e9ecef;
                            margin-bottom: 15px;
                            line-height: 1.6;
                            font-size: 15px;
                        ">
                        {formatted_text}
                        </div>
                        """, unsafe_allow_html=True)

            # Processar geração se botão foi clicado
            if generate_button:
                # Validação com toast apenas quando necessário
                if not text_topic or not text_topic.strip():
                    st.toast(
                        "Por favor, preencha o tema do post!",
                        icon="⚠️")
                    sleep(2)
                elif len(text_topic.strip()) < 5:
                    st.toast(
                        "O tema deve ter pelo menos 5 caracteres!",
                        icon="⚠️")
                    sleep(2)
                elif len(text_topic.strip()) > 500:
                    st.toast(
                        "O tema deve ter no máximo 500 caracteres!",
                        icon="❌")
                    sleep(2)
                else:
                    # Validação passou - processar geração
                    query = search_query if search_query else (
                        text_topic.strip()
                    )
                    platform_code = selected_platform if (
                        selected_platform != "GENERIC"
                    ) else ""

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

        elif 'create' not in permissions:
            st.markdown("""
            <div style="text-align: center; padding: 50px;
                background: #fff3cd; border-radius: 15px;
                border: 1px solid #ffeaa7;">
                <h3 style="color: #856404;">🔒 Acesso Restrito</h3>
                <p style="color: #856404; font-size: 1.1rem;">
                    Você não possui permissão para gerar posts.<br>
                    Entre em contato com o administrador do sistema.
                </p>
            </div>
            """, unsafe_allow_html=True)

    def render(self, token, menu_position, permissions):
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
                st.markdown("""
                <div style="text-align: center; padding: 50px;
                    background: #f8f9fa; border-radius: 15px;
                    border: 2px dashed #dee2e6;">
                    <h3 style="color: #6c757d;">📄 Nenhum post encontrado</h3>
                    <p style="color: #6c757d; font-size: 1.1rem;">
                        Que tal gerar seu primeiro post usando IA?
                    </p>
                    <p style="color: #6c757d;">
                        Vá para <strong>Gerar post</strong> no menu
                        para começar.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                return

            # Filtros
            st.markdown("### 🔍 Filtros")
            col_filter1, col_filter2 = st.columns(2)

            with col_filter1:
                status_filter = st.selectbox(
                    "Status:",
                    ["Todos", "Aprovado", "Pendente"],
                    index=0
                )

            with col_filter2:
                search_text = st.text_input(
                    "🔎 Buscar por tema:",
                    placeholder="Digite palavras-chave do tema..."
                )

            # Filtrar posts
            filtered_texts = texts
            if status_filter != "Todos":
                if status_filter == "Aprovado":
                    filtered_texts = [
                        t for t in filtered_texts if t.get(
                            'is_approved', False)]
                elif status_filter == "Pendente":
                    filtered_texts = [
                        t for t in filtered_texts if not t.get(
                            'is_approved', False)]

            if search_text:
                filtered_texts = [
                    t for t in filtered_texts if search_text.lower() in t.get(
                        'theme', '').lower()]

            if not filtered_texts:
                st.toast(
                    body="Nenhum post encontrado com os filtros aplicados.",
                    icon="🔍"
                )
                sleep(2)
                return

            # Exibir posts em cards
            st.markdown("### 📋 Lista de Posts")

            for i, text in enumerate(filtered_texts):
                # Card do post - mapear is_approved da API para status visual
                is_approved = text.get('is_approved', False)
                status_color = '#28a745' if is_approved else '#ffc107'
                status_emoji = '✅' if is_approved else '⏳'
                status_text = 'Aprovado' if is_approved else 'Pendente'

                # Usar 'content' da API como post gerado
                content_text = text.get('content', text.get(
                    'generated_text', 'Post não disponível'))

                # Container principal do card
                with st.container():
                    # Formatação da data brasileira
                    created_date = text.get('created_at', 'N/A')
                    if created_date != 'N/A' and len(created_date) >= 10:
                        try:
                            from datetime import datetime
                            date_obj = datetime.strptime(
                                created_date[:10],
                                '%Y-%m-%d'
                            )
                            br_date = date_obj.strftime('%d/%m/%Y')
                        except Exception:
                            br_date = created_date[:10]
                    else:
                        br_date = 'N/A'

                    theme_display = text.get('theme', 'Sem título')[:100]
                    theme_display += '...' if (
                        len(text.get('theme', '')) > 100
                    ) else ''

                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(145deg, #ffffff, #f8f9fa);
                        padding: 20px;
                        border-radius: 15px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        border-left: 5px solid {status_color};
                        margin-bottom: 15px;
                        display: flex;
                        gap: 20px;
                    ">
                        <div style="flex: 0 0 300px;">
                            <h4 style="color: #333; margin-bottom: 10px;">
                                {status_emoji} {theme_display}
                            </h4>
                            <p style="color: #666; margin-bottom: 10px;">
                                <strong>Status:</strong> <span style="color: {
                        status_color
                    };">{status_text}</span>
                            </p>
                            <p style="color: #666; margin-bottom: 10px;">
                                <strong>📅 Data:</strong> {br_date}
                            </p>
                            <p style="color: #666; margin-bottom: 15px;">
                                <strong>📱 Plataforma:</strong> {
                        PLATFORMS.get(
                            text.get('platform', 'N/A'), 'N/A')
                    }
                            </p>
                        </div>
                        <div style="
                            flex: 1;
                            background: #f8f9fa;
                            padding: 15px;
                            border-radius: 8px;
                            max-height: 200px;
                            overflow-y: auto;
                            border: 1px solid #dee2e6;
                        ">
                            <h5 style="color: #333; margin-bottom: 10px;">
                                📄 Conteúdo:
                            </h5>
                            <div style="color: #555;
                                font-size: 0.9rem; line-height: 1.4;">
                                {content_text[:500]}{'...' if len(
                        content_text
                    ) > 500 else ''}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Botões de ação para cada post (sempre visíveis)
                    col_btn1, col_btn2, col_btn3 = st.columns(3)

                    text_id = text.get('id')

                    with col_btn1:
                        # Botão aprovar - ativo se não aprovado e tem permissão
                        approve_key = f"approve_{text_id}_{i}"
                        approve_disabled = is_approved or 'update' not in (
                            permissions
                        )
                        approve_type = "secondary" if not (
                            approve_disabled
                        ) else "primary"

                        if st.button(
                            "✅ Aprovar" if not is_approved else "✅ Aprovado",
                            key=approve_key,
                            use_container_width=True,
                            type=approve_type,
                            disabled=approve_disabled,
                                help="Aprovar post" if not (
                                    approve_disabled
                                ) else "Post já aprovado"):
                            with st.spinner("Aprovando post..."):
                                result = TextsRequest().approve_text(
                                    token,
                                    text_id
                                )
                            st.toast(result, icon="✅")
                            sleep(2)
                            st.rerun()

                    with col_btn2:
                        # Botão reprovar - ativo se aprovado e tem permissão
                        reject_key = f"reject_{text_id}_{i}"
                        reject_disabled = not is_approved or 'update' not in (
                            permissions
                        )
                        reject_type = "secondary" if not reject_disabled else (
                            "primary"
                        )

                        if st.button(
                            "❌ Reprovar" if is_approved else "❌ Reprovado",
                            key=reject_key,
                            use_container_width=True,
                            type=reject_type,
                            disabled=reject_disabled,
                                help="Reprovar post" if not (
                                    reject_disabled
                                ) else "Post já reprovado"):
                            with st.spinner("Reprovando post..."):
                                result = TextsRequest().reject_text(
                                    token,
                                    text_id
                                )
                            st.toast(result, icon="❌")
                            sleep(2)
                            st.rerun()

                    with col_btn3:
                        # Botão regenerar - sempre ativo se tem permissão
                        regenerate_key = f"regenerate_{text_id}_{i}"
                        regenerate_disabled = 'create' not in permissions

                        if st.button(
                            "🔄 Regenerar",
                            key=regenerate_key,
                            use_container_width=True,
                            type="secondary",
                            disabled=regenerate_disabled,
                            help="Regenerar este post" if not (
                                regenerate_disabled
                            ) else "Sem permissão para regenerar"
                        ):
                            # Armazenar dados do post para regeneração
                            st.session_state.regenerate_text_data = {
                                'theme': text.get('theme', ''),
                                'original_id': text_id
                            }
                            st.toast(
                                "Dados salvos!",
                                icon="📝"
                            )
                            sleep(2)

            # Paginação simples
            if len(filtered_texts) > 10:
                st.toast(
                    f"""Exibindo {
                        min(10, len(filtered_texts))
                    } de {len(filtered_texts)} posts""",
                    icon="📄")
                sleep(2)

        elif 'read' not in permissions:
            st.markdown("""
            <div style="text-align: center; padding: 50px;
                background: #fff3cd; border-radius: 15px;
                border: 1px solid #ffeaa7;">
                <h3 style="color: #856404;">🔒 Acesso Restrito</h3>
                <p style="color: #856404; font-size: 1.1rem;">
                    Você não possui permissão para visualizar posts.<br>
                    Entre em contato com o administrador do sistema.
                </p>
            </div>
            """, unsafe_allow_html=True)

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
                st.markdown("""
                <div style="text-align: center; padding: 50px;
                    background: #f8f9fa; border-radius: 15px;
                    border: 2px dashed #dee2e6;">
                    <h3 style="color: #6c757d;">📄 Nenhum post encontrado</h3>
                    <p style="color: #6c757d; font-size: 1.1rem;">
                        Não há posts disponíveis para edição.
                    </p>
                </div>
                """, unsafe_allow_html=True)
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
                    help="Selecione um post da lista para editar"
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
                        help="Atualize o tema do post",
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
                        help="Atualize o status do post"
                    )

                    # Converter de volta para o valor da API
                    new_approval_status = new_status_display == "✅ Aprovado"

                    st.markdown("</div>", unsafe_allow_html=True)

                with col_preview:

                    st.subheader("👁️ Prévia das Alterações")

                    # Verificar se houve mudanças
                    has_changes = (
                        new_topic != text_data['theme'] or
                        new_approval_status != text_data.get('is_approved'))

                    if has_changes:
                        st.success("📝 Alterações detectadas!")
                    else:
                        st.info("ℹ️ Nenhuma alteração feita")

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

                    st.markdown("</div>", unsafe_allow_html=True)

                # Validação e botão de atualização
                if new_topic:
                    validated_topic, topic_data = self.validate_topic(
                        new_topic)

                    if validated_topic and has_changes:
                        st.markdown("<br>", unsafe_allow_html=True)
                        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

                        with col_btn2:
                            confirm_button = st.button(
                                "💾 Salvar Alterações",
                                use_container_width=True,
                                type="primary",
                                help="Confirmar as alterações no post"
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
                                    sleep(1)

                                st.toast(
                                    "Post atualizado com sucesso!",
                                    icon="✅"
                                )
                                st.balloons()
                                st.toast(returned_text, icon="ℹ️")
                                sleep(2)
                                st.rerun()

                # Área de prévia do post completo
                with st.expander(
                    "📄 Visualizar Post Completo",
                    expanded=False
                ):
                    content_text = text_data.get(
                        'content', text_data.get(
                            'generated_text', 'Post não disponível'))
                    st.markdown(f"""
                    <div style="
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 10px;
                        max-height: 400px;
                        overflow-y: auto;
                        border: 1px solid #dee2e6;
                    ">
                        {content_text}
                    </div>
                    """, unsafe_allow_html=True)

        elif 'update' not in permissions:
            st.markdown("""
            <div style="text-align: center; padding: 50px;
                background: #fff3cd; border-radius: 15px;
                border: 1px solid #ffeaa7;">
                <h3 style="color: #856404;">🔒 Acesso Restrito</h3>
                <p style="color: #856404; font-size: 1.1rem;">
                    Você não possui permissão para atualizar posts.<br>
                    Entre em contato com o administrador do sistema.
                </p>
            </div>
            """, unsafe_allow_html=True)

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
        col_header, col_menu, col_actions = st.columns([1, 1.2, 1])

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
                    help="Selecione a operação que deseja realizar",
                    label_visibility="collapsed"
                )
            else:
                st.toast(
                    "Você não possui permissões para usar esta funcionalidade",
                    icon="❌")
                sleep(2)
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
