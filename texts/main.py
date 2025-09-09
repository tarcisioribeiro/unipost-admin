import streamlit as st
import pandas as pd
from texts.request import TextsRequest
from dictionary.vars import PLATFORMS
from time import sleep
from services.elasticsearch_service import ElasticsearchService
from services.redis_service import RedisService
from services.text_generation_service import TextGenerationService


class Texts:
    """
    Classe que representa os métodos referentes à geração de texto natural.
    Implementa o fluxo completo conforme roadmap:
    - Busca automática de textos no ElasticSearch
    - Vetorização usando SentenceTransformers
    - Cache dos vetores no Redis
    - Interface para input do usuário
    - Elaboração de contexto de prompt
    - Geração de texto via LLM e webhook
    """

    def __init__(self):
        self.es_service = ElasticsearchService()
        self.redis_service = RedisService()
        self.text_service = TextGenerationService()

    def treat_texts_dataframe(self, texts_data):
        """
        Realiza o tratamento e formatação dos dados referentes aos textos.

        Parameters
        ----------
        texts_data : list
            A série de dados referentes aos textos gerados.

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
                'generated_text': 'Texto Gerado',
                'created_at': 'Data de Criação',
                'status': 'Status',
            }
        )

        df = df[[
            "Tema",
            "Texto Gerado",
            "Data de Criação",
            "Status",
        ]
        ]

        df = df.sort_values(by="Data de Criação", ascending=False)

        return df

    def get_texts_index(self, texts):
        """
        Obtém o índice dos textos, com seus temas e identificadores.

        Parameters
        ----------
        texts : dict
            Dicionário com os dados dos textos.

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
        Valida o tema informado.

        Parameters
        ----------
        topic : str
            O tema para geração de texto.

        Returns
        -------
            bool
            se o tema informado é ou não válido.
            topic : str
            O tema validado.
        """
        if not topic or len(topic.strip()) < 5:
            st.error(
                body="Tema muito curto. Use pelo menos 5 caracteres."
            )
            return False, topic

        if len(topic.strip()) > 500:
            st.error(
                body="Tema muito longo. Use no máximo 500 caracteres."
            )
            return False, topic

        st.success("Tema válido.")
        return True, topic.strip()

    def _process_text_generation(
            self,
            user_topic: str,
            search_query: str,
            token: str):
        """
        Processa a geração completa de texto seguindo o fluxo do roadmap.
        """
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # 1. Verificar cache Redis
            status_text.text("Verificando cache...")
            progress_bar.progress(10)

            cached_data = self.redis_service.get_cached_vectors(search_query)

            if cached_data:
                vectors = cached_data['vectors']
                texts = cached_data['texts']
                status_text.text("Dados encontrados no cache")
            else:
                # 2. Busca automática no ElasticSearch
                status_text.text("Buscando textos no ElasticSearch...")
                progress_bar.progress(20)

                raw_texts = self.es_service.search_texts(search_query)
                if not raw_texts:
                    st.warning("Nenhum texto encontrado no ElasticSearch")
                    return

                # 3. Tratamento dos textos
                status_text.text("Tratando textos...")
                progress_bar.progress(40)

                texts = self.text_service.treat_text_content(raw_texts)
                if not texts:
                    st.warning("Nenhum texto válido após tratamento")
                    return

                # 4. Vetorização usando SentenceTransformers
                status_text.text("Gerando vetores...")
                progress_bar.progress(60)

                vectors = self.text_service.vectorize_texts(texts)
                if not vectors:
                    st.error("Erro na vetorização dos textos")
                    return

                # 5. Cache no Redis
                self.redis_service.cache_vectors(search_query, vectors, texts)

            # 6. Busca de vetores similares ao tema
            status_text.text("Encontrando textos similares...")
            progress_bar.progress(70)

            similar_texts = self.text_service.find_similar_vectors(
                user_topic, vectors, texts)
            if not similar_texts:
                st.warning("Nenhum texto similar encontrado")
                return

            # 7. Elaboração do contexto de prompt
            status_text.text("Criando contexto do prompt...")
            progress_bar.progress(80)

            prompt_context = self.text_service.create_prompt_context(
                user_topic, similar_texts)

            # 8. Geração de texto via LLM
            status_text.text("Gerando texto com LLM...")
            progress_bar.progress(90)

            generated_text = self.text_service.generate_text_via_llm(
                prompt_context
            )
            if not generated_text:
                st.error("Erro na geração de texto via LLM")
                return

            # 9. Envio para aprovação via webhook
            status_text.text("Enviando para aprovação...")
            progress_bar.progress(95)

            approval_sent = self.text_service.send_for_approval(
                generated_text, user_topic)

            # 10. Salvar no banco de dados via API
            text_data = {
                "topic": user_topic,
                "generated_text": generated_text,
                "search_query": search_query,
                "status": "pending_approval" if approval_sent else "generated"
            }

            send_result = TextsRequest().create_text(
                token=token,
                text_data=text_data
            )

            progress_bar.progress(100)
            status_text.text("Processo concluído!")

            st.success("Texto gerado com sucesso!")

            st.subheader("📄 Texto Gerado")
            st.markdown(generated_text)

            if approval_sent:
                st.info("📧 Texto enviado para aprovação manual")
            else:
                st.warning("Erro ao enviar para aprovação")

            st.toast(send_result)

            with st.expander("🔍 Referências Utilizadas"):
                for i, (text, score) in enumerate(similar_texts, start=1):
                    st.write(f"**Referência {i}** (Similaridade: {score:.3f})")
                    st.write(text[:500] + "..." if len(text) > 500 else text)
                    st.divider()

        except Exception as e:
            st.error(f"Erro durante o processamento: {e}")

        finally:
            progress_bar.empty()
            status_text.empty()

    def create(self, token, menu_position, permissions):
        """
        Gera um novo texto usando IA.

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
            with menu_position:
                cl1, cl2 = st.columns(2)
                with cl2:
                    st.subheader("Gerador de Conteúdo")

            # Layout responsivo com duas colunas
            col_input, col_preview = st.columns([1.2, 0.8])

            with col_input:
                st.subheader("📝 Entrada de Dados")

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
                        "automaticamente do texto selecionado."
                    )

                text_topic = st.text_area(
                    label="🎯 Tema do texto",
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

                # Opções avançadas
                with st.expander("⚙️ Configurações Avançadas", expanded=False):
                    tone_options = [
                        "Profissional",
                        "Casual",
                        "Acadêmico",
                        "Criativo",
                        "Técnico"]
                    selected_tone = st.selectbox(
                        "📝 Tom do texto",
                        tone_options,
                        help="Escolha o tom desejado para o texto"
                    )

                    length_options = [
                        "Curto (100-200 palavras)",
                        "Médio (300-500 palavras)",
                        "Longo (500+ palavras)"]
                    selected_length = st.selectbox(
                        "📏 Tamanho aproximado",
                        length_options,
                        index=1,
                        help="Defina o tamanho aproximado do texto"
                    )

                st.markdown("</div>", unsafe_allow_html=True)

                # Validação em tempo real
                if text_topic:
                    if len(text_topic.strip()) < 5:
                        st.warning(
                            "⚠️ O tema deve ter pelo menos 5 caracteres")
                        topic_valid = False
                    elif len(text_topic.strip()) > 500:
                        st.error("❌ O tema deve ter no máximo 500 caracteres")
                        topic_valid = False
                    else:
                        st.success("✅ Tema válido!")
                        topic_valid = True
                else:
                    topic_valid = False

            with col_preview:
                st.subheader("👁️ Prévia dos Dados")

                if text_topic:
                    st.markdown(f"""
                    **🎯 Tema:**
                    {text_topic[:200]}{'...' if len(text_topic) > 200 else ''}

                    **🔍 Busca:** {search_query if search_query else text_topic}

                    **📊 Caracteres:** {len(text_topic)}/500
                    """)

                    if 'selected_tone' in locals():
                        st.markdown(f"**📝 Tom:** {selected_tone}")
                    if 'selected_length' in locals():
                        st.markdown(f"**📏 Tamanho:** {selected_length}")
                else:
                    st.info("💡 Digite um tema para ver a prévia")

                st.markdown("</div>", unsafe_allow_html=True)

            # Botão de geração centralizado
            if text_topic and topic_valid:
                st.markdown("<br>", unsafe_allow_html=True)
                col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
                with col_btn2:
                    generate_button = st.button(
                        "🚀 Gerar Texto com IA",
                        use_container_width=True,
                        type="primary",
                        help="Clique para iniciar a geração do texto usando IA"
                    )

                    if generate_button:
                        query = search_query if (
                            search_query
                        ) else text_topic.strip()

                        # Adicionar configurações avançadas ao contexto se
                        # disponíveis
                        enhanced_topic = text_topic.strip()
                        if 'selected_tone' in locals():
                            enhanced_topic += f" [Tom: {selected_tone}]"
                        if 'selected_length' in locals():
                            enhanced_topic += f" [Tamanho: {selected_length}]"

                        self._process_text_generation(
                            enhanced_topic,
                            query,
                            token
                        )

        elif 'create' not in permissions:
            st.markdown("""
            <div style="text-align: center; padding: 50px;
                background: #fff3cd; border-radius: 15px;
                border: 1px solid #ffeaa7;">
                <h3 style="color: #856404;">🔒 Acesso Restrito</h3>
                <p style="color: #856404; font-size: 1.1rem;">
                    Você não possui permissão para gerar textos.<br>
                    Entre em contato com o administrador do sistema.
                </p>
            </div>
            """, unsafe_allow_html=True)

    def render(self, token, menu_position, permissions):
        """
        Interface para renderização dos textos gerados.

        Parameters
        ----------
        token : str
            O token utilizado no envio da requisição.
        menu_position : Any
            posição do menu superior com a listagem dos textos.
        permissions : list
            Lista contendo as permissões do usuário.
        """
        if 'read' in permissions:
            with menu_position:
                cl1, cl2 = st.columns(2)
                with cl2:
                    st.subheader("📚 Biblioteca de Textos")

            texts = TextsRequest().get_texts(token)

            if not texts:
                st.markdown("""
                <div style="text-align: center; padding: 50px;
                    background: #f8f9fa; border-radius: 15px;
                    border: 2px dashed #dee2e6;">
                    <h3 style="color: #6c757d;">📄 Nenhum texto encontrado</h3>
                    <p style="color: #6c757d; font-size: 1.1rem;">
                        Que tal gerar seu primeiro texto usando IA?
                    </p>
                    <p style="color: #6c757d;">
                        Vá para <strong>Gerar texto</strong> no menu
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

            # Filtrar textos
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
                st.info("🔍 Nenhum texto encontrado com os filtros aplicados.")
                return

            # Exibir textos em cards
            st.markdown("### 📋 Lista de Textos")

            for i, text in enumerate(filtered_texts):
                # Card do texto - mapear is_approved da API para status visual
                is_approved = text.get('is_approved', False)
                status_color = '#28a745' if is_approved else '#ffc107'
                status_emoji = '✅' if is_approved else '⏳'
                status_text = 'Aprovado' if is_approved else 'Pendente'

                # Usar 'content' da API como texto gerado
                content_text = text.get('content', text.get(
                    'generated_text', 'Texto não disponível'))

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
                        except:
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

                    # Botões de ação para cada texto
                    col_btn1, col_btn2, col_btn3, col_space = st.columns(
                        [1, 1, 1, 2]
                    )

                    text_id = text.get('id')

                    with col_btn1:
                        if not is_approved and 'update' in permissions:
                            approve_key = f"approve_{text_id}_{i}"
                            if st.button(
                                "✅ Aprovar",
                                key=approve_key,
                                use_container_width=True,
                                type="secondary"
                            ):
                                with st.spinner("Aprovando texto..."):
                                    result = TextsRequest().approve_text(
                                        token,
                                        text_id
                                    )
                                st.success(result)
                                sleep(1)
                                st.rerun()

                    with col_btn2:
                        if is_approved and 'update' in permissions:
                            reject_key = f"reject_{text_id}_{i}"
                            if st.button(
                                "❌ Reprovar",
                                key=reject_key,
                                use_container_width=True,
                                type="secondary"
                            ):
                                with st.spinner("Reprovando texto..."):
                                    result = TextsRequest().reject_text(
                                        token,
                                        text_id
                                    )
                                st.warning(result)
                                sleep(1)
                                st.rerun()

                    with col_btn3:
                        if 'create' in permissions:
                            regenerate_key = f"regenerate_{text_id}_{i}"
                            if st.button(
                                "🔄 Regenerar",
                                key=regenerate_key,
                                use_container_width=True,
                                type="secondary"
                            ):
                                # Armazenar dados do texto para regeneração
                                st.session_state.regenerate_text_data = {
                                    'theme': text.get('theme', ''),
                                    'original_id': text_id
                                }
                                st.info(
                                    "📝 Use o tema salvo na seção " +
                                    "'Gerar Novo Texto' para regenerar " +
                                    "este conteúdo."
                                )
                                sleep(1.5)

            # Paginação simples
            if len(filtered_texts) > 10:
                st.info(
                    f"📄 Exibindo {min(10, len(filtered_texts))} de "
                    f"{len(filtered_texts)} textos")

        elif 'read' not in permissions:
            st.markdown("""
            <div style="text-align: center; padding: 50px;
                background: #fff3cd; border-radius: 15px;
                border: 1px solid #ffeaa7;">
                <h3 style="color: #856404;">🔒 Acesso Restrito</h3>
                <p style="color: #856404; font-size: 1.1rem;">
                    Você não possui permissão para visualizar textos.<br>
                    Entre em contato com o administrador do sistema.
                </p>
            </div>
            """, unsafe_allow_html=True)

    def update(self, token, menu_position, permissions):
        """
        Menu com interface para atualização do texto.

        Parameters
        ----------
        token : str
            O token utilizado no envio da requisição.
        menu_position : Any
            posição do menu superior com a listagem dos textos.
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
                    <h3 style="color: #6c757d;">📄 Nenhum texto encontrado</h3>
                    <p style="color: #6c757d; font-size: 1.1rem;">
                        Não há textos disponíveis para edição.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                return

            # Seleção do texto no menu superior
            with menu_position:
                st.markdown("### 🎯 Selecionar Texto")
                texts_options = {}
                for text in texts:
                    theme_preview = text['theme'][:50]
                    theme_preview += '...' if len(text['theme']) > 50 else ''
                    status = ('Aprovado' if text.get('is_approved')
                              else 'Pendente')
                    key = f"{theme_preview} ({status})"
                    texts_options[key] = text['id']

                selected_text_display = st.selectbox(
                    "Escolha o texto para editar:",
                    options=list(texts_options.keys()),
                    help="Selecione um texto da lista para editar"
                )
                selected_text_id = texts_options[selected_text_display]

            # Interface de edição
            text_data = TextsRequest().get_text(token, selected_text_id)

            if text_data:
                col_form, col_preview = st.columns([1, 1])

                with col_form:
                    st.subheader("📝 Dados do Texto")

                    new_topic = st.text_area(
                        label="🎯 Tema",
                        value=text_data['theme'],
                        max_chars=500,
                        help="Atualize o tema do texto",
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
                        help="Atualize o status do texto"
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

                    st.markdown(f"""
                    **🎯 Novo Tema:**
                    {
                        new_topic[
                            :200
                        ]
                    }{'...' if len(
                        new_topic
                    ) > 200 else ''}

                    **📊 Novo Status:**
                    {status_options[new_approval_status]}

                    **📅 Data Original:**
                    {text_data.get('created_at', 'N/A')[:10]}

                    **📊 Caracteres:** {len(new_topic)}/500""")  # type: ignore

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
                                help="Confirmar as alterações no texto"
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

                                st.success("✅ Texto atualizado com sucesso!")
                                st.balloons()
                                st.toast(returned_text)
                                sleep(1.5)
                                st.rerun()

                # Área de prévia do texto completo
                with st.expander(
                    "📄 Visualizar Texto Completo",
                    expanded=False
                ):
                    content_text = text_data.get(
                        'content', text_data.get(
                            'generated_text', 'Texto não disponível'))
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
                    Você não possui permissão para atualizar textos.<br>
                    Entre em contato com o administrador do sistema.
                </p>
            </div>
            """, unsafe_allow_html=True)

    def main_menu(self, token, permissions):
        """
        Menu principal da aplicação de geração de textos.

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

        with col_header:
            st.markdown("""
            <div style="padding: 10px 0;">
                <h2 style="color: #1f77b4; margin: 0;">🤖 UniPost</h2>
            </div>
            """, unsafe_allow_html=True)

        with col_menu:
            # Menu com ícones mais intuitivos
            menu_options = {
                "📚 Biblioteca de Textos": self.render,
                "🚀 Gerar Novo Texto": self.create,
                "✏️ Editar Texto": self.update,
            }

            # Verificar permissões e filtrar opções disponíveis
            available_options = {}
            if 'read' in class_permissions:
                available_options["📚 Biblioteca de Textos"] = (
                    menu_options["📚 Biblioteca de Textos"]
                )
            if 'create' in class_permissions:
                available_options["🚀 Gerar Novo Texto"] = (
                    menu_options["🚀 Gerar Novo Texto"]
                )
            if 'update' in class_permissions:
                available_options["✏️ Editar Texto"] = (
                    menu_options["✏️ Editar Texto"]
                )

            if available_options:
                selected_option = st.selectbox(
                    label="Escolha uma ação:",
                    options=list(available_options.keys()),
                    help="Selecione a operação que deseja realizar",
                    label_visibility="collapsed"
                )
            else:
                st.error(
                    "❌ Você não possui permissões para usar esta "
                    "funcionalidade")
                return

        # Mostrar informações de permissão
        with col_actions:
            permission_status = []
            if 'read' in class_permissions:
                permission_status.append("👁️ Visualizar")
            if 'create' in class_permissions:
                permission_status.append("➕ Criar")
            if 'update' in class_permissions:
                permission_status.append("✏️ Editar")
            if 'delete' in class_permissions:
                permission_status.append("🗑️ Excluir")

        st.divider()

        # Executar a opção selecionada
        if available_options:
            executed_option = available_options[selected_option]
            executed_option(
                token=token,
                menu_position=col_actions,
                permissions=class_permissions
            )
