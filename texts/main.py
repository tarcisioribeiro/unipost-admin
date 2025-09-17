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
        """
        # Interface de progresso simplificada
        with result_container.container():
            # Cabeçalho do processo
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem;
                border-radius: 8px;
                text-align: center;
                margin-bottom: 1rem;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            ">
                <h3 style="
                    color: white;
                    margin: 0 0 0.5rem 0;
                    font-size: 1.3rem;
                    font-weight: 600;
                ">
                    🚀 Gerando Post com IA
                </h3>
                <p style="
                    color: rgba(255,255,255,0.9);
                    margin: 0;
                    font-size: 1rem;
                ">
                    Processando sua solicitação...
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Container para progresso
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()

        try:
            # 1. Verificar cache Redis
            status_text.markdown("""
            <div style="
                background: #e3f2fd;
                padding: 0.75rem;
                border-radius: 6px;
                border-left: 4px solid #2196f3;
            ">
                🔍 <strong>Verificando cache Redis...</strong>
            </div>
            """, unsafe_allow_html=True)
            progress_bar.progress(10)

            cached_embeddings = self.redis_service.get_cached_embeddings(
                search_query
            )

            if cached_embeddings:
                similar_texts = cached_embeddings.get('similar_texts', [])
                status_text.markdown("""
                <div style="
                    background: #d4edda;
                    padding: 0.75rem;
                    border-radius: 6px;
                    border-left: 4px solid #28a745;
                ">
                    ✅ <strong>Embeddings encontrados no cache!</strong>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 2. Busca via API de embeddings (por palavras individuais)
                status_text.text(
                    "🔍 Buscando embeddings por palavras individuais..."
                )
                progress_bar.progress(30)

                # Consultar por palavras individuais
                embeddings_by_word = self.embeddings_service.query_embeddings_by_individual_words(  # noqa: E501
                    search_query
                )

                # Agregar todos os resultados para manter compatibilidade
                raw_texts = []
                for word, word_embeddings in embeddings_by_word.items():
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

                # Armazenar dados detalhados para mostrar depois
                st.session_state['detailed_embeddings'] = embeddings_by_word

                # Permite geração mesmo sem resultados da API
                if raw_texts:
                    # 3. Tratamento dos textos da API
                    status_text.text("⚙️ Tratando textos encontrados...")
                    progress_bar.progress(50)

                    texts = self.text_service.treat_text_content(raw_texts)

                    if texts:
                        # 4. Busca de textos similares via API
                        status_text.text("🎯 Encontrando textos similares...")
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

                            # Mostrar preview dos embeddings encontrados
                            status_text.markdown(f"""
                            ✅ **{len(similar_texts)} embeddings encontrados!**

                            **Top 3 referências mais relevantes:**
                            """)

                            for i, (
                                text,
                                score
                            ) in enumerate(similar_texts[:3], 1):
                                title = text.get('title', 'Sem título')
                                text_type = text.get('type', 'Conteúdo')
                                score_percentage = round(score * 100, 1)

                                status_text.markdown(f"""
                                **{i}.** {title} *(Relevância: {
                                    score_percentage
                                }%)*
                                📂 {text_type}
                                """)

                            # Pequena pausa para permitir visualização
                            import time
                            time.sleep(2)
                        else:
                            st.toast(
                                "Nenhuma referência similar encontrada",
                                icon="ℹ️"
                            )
                            similar_texts = []
                    else:
                        st.toast(
                            """Textos inválidos após tratamento,
                            prosseguindo sem referências""",
                            icon="⚠️")
                        similar_texts = []
                else:
                    st.toast(
                        """Nenhuma referência encontrada na API,
                        gerando baseado apenas no tema""",
                        icon="ℹ️")
                    similar_texts = []

            # 6. Elaboração do contexto de prompt com novos parâmetros
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

            # 7. Geração de post via OpenAI/LLM
            status_text.text("🤖 Gerando post com IA...")
            progress_bar.progress(90)

            generated_text = self.text_service.generate_text_via_llm(
                prompt_context
            )
            if not generated_text:
                st.toast("Erro na geração de post via IA", icon="❌")
                return

            # 8. Salvar no banco de dados da API UniPost (SEM EMBEDDING)
            status_text.text("💾 Salvando post no banco de dados...")
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
            status_text.text(
                "✅ Post salvo! Embedding será gerado após aprovação."
            )

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

                # Seção de ações com estilo melhorado
                st.markdown("""
                <div style="
                    background-color: #f8f9fa;
                    padding: 1rem;
                    border-radius: 10px;
                    margin: 1.5rem 0;
                    border-left: 4px solid #667eea;
                ">
                    <h4 style="
                        color: #333;
                        margin: 0 0 1rem 0;
                        font-size: 1.1rem;
                        font-weight: 600;
                    ">
                        🎛️ Ações Disponíveis
                    </h4>
                </div>
                """, unsafe_allow_html=True)

                col_approve, col_reject, col_regenerate = st.columns(3)

                # Botão Aprovar - Gerar embedding quando aprovado
                with col_approve:
                    if st.button(
                        "✅ Aprovar & Gerar Embedding",
                        key="approve_generated",
                        use_container_width=True,
                        type="primary",
                        help="Aprovar post e gerar embedding"
                    ):
                        # Aprovar post e gerar embedding
                        if created_text_id:
                            with st.spinner(
                                "Aprovando post e gerando embedding..."
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
                        help="Marcar como reprovado"
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
                        st.rerun()

                # Referências detalhadas com embeddings encontrados
                if similar_texts:
                    with st.expander(f"""📖 Embeddings Encontrados ({
                        len(similar_texts)
                    } referências)""", expanded=True
                    ):
                        st.markdown("### 🔍 Referências utilizadas na geração:")

                        for i, (
                            text,
                            score
                        ) in enumerate(similar_texts[:5], 1):
                            # Informações do embedding com metadados
                            title = text.get('title', 'Sem título')
                            text_type = text.get('type', 'Conteúdo Geral')
                            index_source = text.get('index', 'unknown')
                            text_content = text.get('text', '')[:300]

                            # Extrair metadados do embedding
                            metadata = text.get('metadata', {})
                            platform = metadata.get(
                                'platform_display',
                                text.get('platform', '')
                            )
                            theme = metadata.get(
                                'theme',
                                text.get('theme', '')
                            )
                            author = metadata.get(
                                'author',
                                text.get('author', '')
                            )
                            origin = text.get('origin', '')
                            created_date = text.get('created_at', '')

                            # Campos específicos dos metadados
                            tags = metadata.get('tags', '')
                            word_count = metadata.get('word_count', '')
                            length = metadata.get('length', '')

                            # Score em porcentagem para melhor visualização
                            score_percentage = round(score * 100, 1)

                            # Score armazenado para uso futuro

                            with st.container():
                                st.markdown(f"**📄 {title}**")

                                col_info, col_score = st.columns([3, 1])

                                with col_info:
                                    # Exibir metadados principais
                                    metadata_info = []
                                    if platform:
                                        metadata_info.append(f"📱 {platform}")
                                    if theme:
                                        metadata_info.append(f"🎯 {theme}")
                                    if origin:
                                        metadata_info.append(f"🗂️ {origin}")

                                    if metadata_info:
                                        st.caption(" • ".join(metadata_info))
                                    else:
                                        st.caption(
                                            f"""🏷️ {
                                                text_type
                                            } • 🗂️ {index_source}"""
                                        )

                                with col_score:
                                    if score >= 0.7:
                                        st.success(
                                            f"Alta: {score_percentage}%"
                                        )
                                    elif score >= 0.4:
                                        st.warning(
                                            f"Média: {score_percentage}%"
                                        )
                                    else:
                                        st.info(f"Baixa: {score_percentage}%")

                                # Seção expandida com mais metadados
                                with st.expander(
                                    "📋 Ver detalhes completos",
                                    expanded=False
                                ):
                                    col_meta1, col_meta2 = st.columns(2)

                                    with col_meta1:
                                        if author:
                                            st.markdown(
                                                f"**👤 Autor:** {author}"
                                            )
                                        if created_date:
                                            try:
                                                from datetime import datetime
                                                if len(created_date) >= 10:
                                                    date_obj = (
                                                        datetime.strptime(
                                                            created_date[:10],
                                                            '%Y-%m-%d'
                                                        )
                                                    )
                                                    br_date = (
                                                        date_obj.strftime(
                                                            '%d/%m/%Y'
                                                        )
                                                    )
                                                    st.markdown(
                                                        f"""**📅 Criado em:** {
                                                            br_date
                                                        }"""
                                                    )
                                            except Exception:
                                                st.markdown(
                                                    f"""**📅 Criado em:** {
                                                        created_date[:10]
                                                    }"""
                                                )
                                        if tags:
                                            st.markdown(f"**🏷️ Tags:** {tags}")

                                    with col_meta2:
                                        if word_count:
                                            st.markdown(
                                                f"**📊 Palavras:** {word_count}"
                                            )
                                        if length:
                                            st.markdown(
                                                f"**📏 Tamanho:** {length}"
                                            )
                                        st.markdown(
                                            f"""**🆔 ID:** {
                                                text.get('id', 'N/A')}"""
                                        )

                                st.markdown(
                                    "**Conteúdo utilizado como referência:**"
                                )
                                st.text(
                                    f"""{
                                        text_content
                                    }{'...' if len(
                                        text.get('text', '')
                                    ) > 300 else ''}"""
                                )
                                st.divider()

                        if len(similar_texts) > 5:
                            st.info(
                                f"""Mostrando 5 de {
                                    len(similar_texts)
                                } referências encontradas.
                                As referências com maior score de
                                similaridade foram priorizadas."""
                            )

                        # Resumo estatístico dos embeddings
                        st.markdown("---")
                        st.markdown("### 📊 Resumo das Referências:")

                        (
                            col_stats1, col_stats2, col_stats3, col_stats4
                        ) = st.columns(4)

                        with col_stats1:
                            st.metric(
                                "Total de Referências", len(similar_texts)
                            )

                        with col_stats2:
                            avg_score = sum(
                                score for _, score in similar_texts
                            ) / len(similar_texts)
                            st.metric("Score Médio", f"{avg_score:.2f}")

                        with col_stats3:
                            high_relevance = sum(
                                1 for _, score in similar_texts if (
                                    score >= 0.7
                                ))
                            st.metric("Alta Relevância", high_relevance)

                        with col_stats4:
                            # Contar tipos únicos de referências
                            unique_types = set(
                                text.get(
                                    'type',
                                    'Geral'
                                ) for text, _ in similar_texts)
                            st.metric("Tipos de Fonte", len(unique_types))

                        # Mostrar tipos de fontes encontradas
                        if len(unique_types) > 1:
                            st.markdown("**🗂️ Tipos de fontes consultadas:**")
                            types_text = ", ".join(sorted(unique_types))
                            st.caption(types_text)
                else:
                    # Exibir aviso quando não há referências
                    with st.expander(
                        "📖 Embeddings Encontrados (0 referências)",
                        expanded=True
                    ):
                        st.warning("""
                        🔍 **Nenhuma referência encontrada**

                        Este post foi gerado baseado apenas no tema fornecido,
                        sem utilizar referências do banco de dados
                        de embeddings.

                        **Possíveis motivos:**
                        - Tema muito específico ou novo
                        - Base de dados ainda não contém conteúdo relacionado
                        - Termos de busca não encontraram correspondências

                        **Dica:** Tente reformular o tema ou usar termos
                        mais gerais para encontrar referências relacionadas.
                        """)

                        # Estatísticas quando não há referências
                        (
                            col_empty1, col_empty2, col_empty3, col_empty4
                        ) = st.columns(4)

                        with col_empty1:
                            st.metric("Total de Referências", 0)
                        with col_empty2:
                            st.metric("Score Médio", "N/A")
                        with col_empty3:
                            st.metric("Alta Relevância", 0)
                        with col_empty4:
                            st.metric("Tipos de Fonte", 0)

                # Mostrar resultado do registro na API
                if send_result.get("success"):
                    st.success("✅ **Texto registrado com sucesso na API!**")
                    if created_text_id:
                        st.info(f"🆔 **ID do texto**: {created_text_id}")
                else:
                    st.error(
                        f"""🚨 **Erro no Registro da API**\n\n{send_result.get(
                            'message',
                            'Erro desconhecido'
                            )
                        }"""
                    )

                # Nova seção: Referências Detalhadas por Palavra
                st.divider()
                st.markdown("## 📚 Referências Detalhadas por Palavra")

                # Verificar se há dados detalhados dos embeddings
                detailed_embeddings = st.session_state.get(
                    'detailed_embeddings',
                    {}
                )

                if detailed_embeddings:
                    # Mostrar estatísticas gerais
                    total_words = len(detailed_embeddings)
                    total_refs = sum(
                        len(refs) for refs in detailed_embeddings.values()
                    )

                    col_stats1, col_stats2, col_stats3 = st.columns(3)
                    with col_stats1:
                        st.metric("🔤 Palavras Consultadas", total_words)
                    with col_stats2:
                        st.metric("📄 Total Referências", total_refs)
                    with col_stats3:
                        avg_refs = total_refs / total_words if (
                            total_words > 0
                        ) else 0
                        st.metric("📊 Média por Palavra", f"{avg_refs:.1f}")

                    st.markdown("---")

                    # Mostrar detalhes por palavra
                    for word, word_refs in detailed_embeddings.items():
                        if word_refs:  # Só mostrar palavras com referências
                            with st.expander(
                                f"""🔍 **{
                                    word.title()
                                }** ({len(word_refs)} referências)""",
                                expanded=False
                            ):
                                for i, ref in enumerate(word_refs[:3], 1):
                                    title = ref.get('title', 'Sem título')
                                    content = ref.get('content', '')[:200]
                                    score = ref.get('similarity_score', 0)
                                    origin = ref.get('origin', 'unknown')

                                    # Card da referência
                                    with st.container():
                                        st.markdown(f"**#{i} {title}**")
                                        st.text(f"{content}...")
                                        col_score, col_origin = st.columns(2)
                                        with col_score:
                                            st.caption(f"📈 Score: {score:.2f}")
                                        with col_origin:
                                            st.caption(f"🔗 Origem: {origin}")
                else:
                    st.info(
                        """📭 Nenhuma referência detalhada """ +
                        """disponível para esta consulta."""
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
                # Cabeçalho da seção de parâmetros
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, \
#764ba2 100%);
                    padding: 1.5rem;
                    border-radius: 12px;
                    margin-bottom: 1.5rem;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                ">
                    <h3 style="
                        color: white;
                        margin: 0;
                        font-size: 1.5rem;
                        font-weight: 600;
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                    ">
                        🎨 Parâmetros de Geração
                    </h3>
                </div>
                """, unsafe_allow_html=True)

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

                # Tooltip personalizado para o campo tema
                st.markdown("""
                <div class="tooltip" style="width: 100%; \
margin-bottom: 0.5rem;">
                    <span style="font-weight: 500; color: #333;">\
🎯 Tema do post</span>
                    <span class="tooltiptext">
                        📝 Dicas para um bom tema:<br>
                        • Seja específico e claro<br>
                        • Use palavras-chave relevantes<br>
                        • Entre 10-100 palavras<br>
                        • Evite termos muito técnicos
                    </span>
                </div>
                """, unsafe_allow_html=True)

                text_topic = st.text_area(
                    label="",
                    value=default_theme,
                    max_chars=500,
                    placeholder="Ex: Benefícios da energia renovável para o \
meio ambiente e economia",
                    help="Descreva detalhadamente o tema que deseja abordar. \
Seja específico para melhores resultados.",
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

                # Botão de geração
                generate_button = st.button(
                    "🚀 Gerar Post com IA",
                    use_container_width=True,
                    type="primary",
                    key="generate_btn",
                    help="Clique para gerar o post com os parâmetros \
configurados"
                )

            # Área de resultado com estilo
            with col_result:
                # Cabeçalho da seção de resultado
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #28a745 0%, \
#20c997 100%);
                    padding: 1.5rem;
                    border-radius: 12px;
                    margin-bottom: 1.5rem;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                ">
                    <h3 style="
                        color: white;
                        margin: 0;
                        font-size: 1.5rem;
                        font-weight: 600;
                        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                    ">
                        📄 Resultado da Geração
                    </h3>
                </div>
                """, unsafe_allow_html=True)

                result_container = st.container()

                # Estado inicial com estilo
                if not generate_button and 'last_generated' not in (
                    st.session_state
                ):
                    with result_container:
                        st.markdown("""
                        <div style="
                            background-color: #e3f2fd;
                            padding: 2rem;
                            border-radius: 10px;
                            text-align: center;
                            margin: 1rem 0;
                            border: 2px dashed #90caf9;
                        ">
                            <h4 style="
                                color: #1976d2;
                                margin-bottom: 1rem;
                                font-weight: 500;
                            ">
                                🤖 Aguardando Geração
                            </h4>
                            <p style="
                                color: #666;
                                margin: 0;
                                font-size: 1rem;
                                line-height: 1.5;
                            ">
                                Configure os parâmetros ao lado e clique em \
<strong>"🚀 Gerar Post"</strong><br>
                                para criar seu conteúdo com inteligência \
artificial.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

                # Exibir último resultado se existe
                elif 'last_generated' in st.session_state:
                    last_data = st.session_state['last_generated']
                    with result_container:
                        st.toast("Post anterior carregado", icon="📄")

                        # Mostrar informações do post anterior
                        st.info(f"""
                        📱 {
                            last_data.get('platform', 'N/A')
                        } • 📝 {last_data.get('tone', 'N/A').title()} •
                        🎨 {last_data.get('creativity', 'N/A').title()} • 📏 {
                            last_data.get('length', 'N/A')
                        }
                        """)

                        # Mostrar texto anterior
                        with st.container():
                            st.markdown("**📄 Post Anterior:**")
                            st.markdown(last_data.get('text', ''))

            # Processar geração se botão foi clicado
            if generate_button:
                # Marcar como gerando
                st.session_state.generating = True

                # Validação com feedback visual melhorado
                if not text_topic or not text_topic.strip():
                    st.session_state.generating = False
                    st.error("⚠️ **Campo obrigatório**: Por favor, preencha o \
tema do post!")
                elif len(text_topic.strip()) < 5:
                    st.session_state.generating = False
                    st.warning(
                        "⚠️ **Tema muito curto**: " +
                        "O tema deve ter pelo menos 5 caracteres!"
                    )
                elif len(text_topic.strip()) > 500:
                    st.session_state.generating = False
                    st.error(
                        "❌ **Tema muito longo**: O tema deve ter no máximo "
                        "500 caracteres!"
                    )
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

            Você não possui permissão para gerar posts.
            Entre em contato com o administrador do sistema.
            """)

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
                col4, col5, col6 = st.columns(3)
                with col5:
                    st.info("""
                    **📄 Nenhum post encontrado**

                    Que tal gerar seu primeiro post usando IA?

                    Vá para **Gerar post** no menu para começar.
                    """)
                return

            # Filtros compactos
            col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 1])

            with col_filter1:
                search_text = st.text_input(
                    "🔎 Buscar:",
                    placeholder="Digite palavras-chave...",
                    label_visibility="collapsed"
                )

            with col_filter2:
                status_filter = st.selectbox(
                    "Status",
                    ["Todos", "Aprovado", "Pendente"],
                    index=0,
                    label_visibility="collapsed"
                )

            with col_filter3:
                st.metric("Total", len(texts))

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
                return

            # Lista de posts com cards estilizados
            for i, text in enumerate(filtered_texts):
                is_approved = text.get('is_approved', False)
                status_emoji = '✅' if is_approved else '⏳'

                # Status badge estilizado
                status_class = 'status-approved' if is_approved else \
                    'status-pending'
                status_text_display = 'Aprovado' if is_approved else 'Pendente'

                # Formatação da data
                created_date = text.get('created_at', 'N/A')
                if created_date != 'N/A' and len(created_date) >= 10:
                    try:
                        from datetime import datetime
                        date_obj = datetime.strptime(
                            created_date[:10],
                            '%Y-%m-%d'
                        )
                        br_date = date_obj.strftime('%d/%m')
                    except Exception:
                        br_date = created_date[8:10] + '/' + created_date[5:7]
                else:
                    br_date = '--'

                theme_display = text.get('theme', 'Sem título')
                content_text = text.get(
                    'content',
                    text.get('generated_text', '')
                )
                word_count = len(content_text.split()) if content_text else 0

                # Card estilizado com hover effect
                st.markdown(f"""
                <div class="hover-card" style="
                    background: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    margin: 1rem 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    border-left: 4px solid \
{'#28a745' if is_approved else '#ffc107'};
                    transition: all 0.3s ease;
                ">
                    <div style="display: flex; justify-content: \
space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; \
margin-bottom: 0.5rem;">
                                <span class="status-badge {status_class}">\
{status_text_display}</span>
                                <span style="margin-left: 1rem; \
font-size: 0.9rem; color: #666;">
                                    📅 {br_date} • 📱 \
{PLATFORMS.get(text.get('platform', 'N/A'), 'Genérico')} \
• 📝 {word_count} palavras
                                </span>
                            </div>
                            <h4 style="
                                color: #333;
                                margin: 0.5rem 0;
                                font-size: 1.1rem;
                                font-weight: 600;
                                line-height: 1.4;
                            ">
                                {status_emoji} {theme_display[:80]}\
{'...' if len(theme_display) > 80 else ''}
                            </h4>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Seção de ações com layout melhorado
                text_id = text.get('id')
                col_btn1, col_btn2, col_btn3 = st.columns(3)

                with col_btn1:
                    if not is_approved and 'update' in permissions:
                        if st.button(
                            "✅ Aprovar",
                            key=f"approve_{text_id}_{i}",
                            help="Aprovar & Gerar Embedding",
                            use_container_width=True,
                            type="primary"
                        ):
                            with st.spinner(
                                "Aprovando e gerando embedding..."
                            ):
                                text_content = text.get('content', '')
                                text_theme = text.get('theme', '')
                                result = \
                                    TextsRequest().\
                                    approve_and_generate_embedding(
                                        token,
                                        text_id,
                                        text_content,
                                        text_theme
                                    )
                            st.toast(result, icon="✅")
                            st.rerun()
                    elif is_approved and 'update' in permissions:
                        if st.button(
                            "❌ Reprovar",
                            key=f"reject_{text_id}_{i}",
                            help="Reprovar",
                            use_container_width=True,
                            type="secondary"
                        ):
                            with st.spinner("Reprovando..."):
                                result = TextsRequest().reject_text(
                                    token,
                                    text_id
                                )
                            st.toast(result, icon="❌")
                            st.rerun()

                with col_btn2:
                    if 'create' in permissions:
                        if st.button(
                            "🔄 Regenerar",
                            key=f"regenerate_{text_id}_{i}",
                            help="Regenerar",
                            use_container_width=True,
                            type="secondary"
                        ):
                            st.session_state.regenerate_text_data = {
                                'theme': text.get('theme', ''),
                                'original_id': text_id
                            }
                            st.toast(
                                "Carregado para regeneração",
                                icon="🔄"
                            )

                with col_btn3:
                    # Botão para visualizar conteúdo
                    if st.button(
                        "👁️ Visualizar",
                        key=f"view_{text_id}_{i}",
                        help="Ver conteúdo completo",
                        use_container_width=True,
                        type="secondary"
                    ):
                        # Toggle do estado de visualização
                        view_key = f"view_expanded_{text_id}"
                        if view_key not in st.session_state:
                            st.session_state[view_key] = False
                        st.session_state[
                            view_key
                        ] = not st.session_state[view_key]

                # Conteúdo expandido condicionalmente com animação
                view_key = f"view_expanded_{text_id}"
                if st.session_state.get(view_key, False):
                    st.markdown("""
                    <div style="
                        background: #f8f9fa;
                        padding: 1.5rem;
                        border-radius: 10px;
                        margin: 1rem 0;
                        border: 1px solid #e9ecef;
                        animation: fadeIn 0.5s ease-out;
                    ">
                        <h5 style="
                            color: #333;
                            margin: 0 0 1rem 0;
                            font-weight: 600;
                        ">
                            📄 Conteúdo Completo do Post
                        </h5>
                    </div>
                    """, unsafe_allow_html=True)

                    st.text_area(
                        "",
                        value=content_text,
                        height=150,
                        disabled=True,
                        label_visibility="collapsed",
                        key=f"full_{i}"
                    )

                    st.divider()

            # Estatísticas da listagem
            if filtered_texts:
                total_approved = len(
                    [t for t in filtered_texts if t.get('is_approved', False)]
                )
                total_pending = len(filtered_texts) - total_approved

                col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                with col_stats1:
                    st.metric("Total Filtrados", len(filtered_texts))
                with col_stats2:
                    st.metric("Aprovados", total_approved)
                with col_stats3:
                    st.metric("Pendentes", total_pending)
                with col_stats4:
                    approval_rate = (
                        total_approved / len(
                            filtered_texts
                        ) * 100
                    ) if filtered_texts else 0
                    st.metric("Taxa Aprovação", f"{approval_rate:.0f}%")

        elif 'read' not in permissions:
            st.warning("""
            **🔒 Acesso Restrito**

            Você não possui permissão para visualizar posts.
            Entre em contato com o administrador do sistema.
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
                col4, col5, col6 = st.columns(3)
                with col5:
                    st.info("""
                    **📄 Nenhum post encontrado**

                    Não há posts disponíveis para edição.
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
                        disabled=True,
                        label_visibility="collapsed"
                    )

        elif 'update' not in permissions:
            st.warning("""
            **🔒 Acesso Restrito**

            Você não possui permissão para atualizar posts.
            Entre em contato com o administrador do sistema.
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
