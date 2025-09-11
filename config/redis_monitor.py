import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Any
from services.redis_service import RedisService
import logging

logger = logging.getLogger(__name__)


class RedisMonitor:
    """
    Módulo para monitoramento e consulta do Redis.
    Permite visualizar dados em cache,
    fazer consultas e verificar saúde da conexão.
    """

    def __init__(self):
        """Inicializa o monitor do Redis."""
        self.redis_service = RedisService()

    def check_redis_health(self) -> Dict[str, Any]:
        """
        Verifica a saúde da conexão com Redis.

        Returns
        -------
        Dict[str, Any]
            Status de saúde do Redis
        """
        try:
            # Teste básico de conexão
            if self.redis_service.redis_client:
                # Ping test
                response = self.redis_service.redis_client.ping()
                if response:
                    # Obter informações do servidor
                    info = self.redis_service.redis_client.info()

                    return {
                        "status": "healthy",
                        "ping": True,
                        "info": info,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "error",
                        "ping": False,
                        "error": "Ping failed",
                        "timestamp": datetime.now().isoformat()
                    }
            else:
                return {
                    "status": "connection_error",
                    "error": "Redis client not initialized",
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error checking Redis health: {e}")
            return {
                "status": "connection_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def get_all_keys(self, pattern: str = "*") -> List[str]:
        """
        Obtém todas as chaves que correspondem ao padrão.

        Parameters
        ----------
        pattern : str
            Padrão para buscar chaves (default: "*")

        Returns
        -------
        List[str]
            Lista de chaves encontradas
        """
        try:
            if self.redis_service.redis_client:
                keys = self.redis_service.redis_client.keys(pattern)
                # Decodificar bytes para strings
                return [
                    key.decode(
                        'utf-8'
                    ) if isinstance(key, bytes) else key for key in keys]
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting Redis keys: {e}")
            return []

    def get_key_info(self, key: str) -> Dict[str, Any]:
        """
        Obtém informações detalhadas sobre uma chave.

        Parameters
        ----------
        key : str
            Nome da chave

        Returns
        -------
        Dict[str, Any]
            Informações da chave
        """
        try:
            if not self.redis_service.redis_client:
                return {"error": "Redis client not available"}

            client = self.redis_service.redis_client

            # Verificar se a chave existe
            if not client.exists(key):
                return {"error": "Key does not exist"}

            # Obter tipo da chave
            key_type = client.type(key).decode('utf-8')

            # Obter TTL
            ttl = client.ttl(key)

            # Obter tamanho em memória
            try:
                memory_usage = client.memory_usage(key)
            except Exception:
                memory_usage = "N/A"

            info = {
                "key": key,
                "type": key_type,
                "ttl": ttl,
                "memory_usage": memory_usage,
                "exists": True
            }

            # Obter valor baseado no tipo
            try:
                if key_type == "string":
                    value = client.get(key)
                    if value:
                        value = value.decode('utf-8')
                        # Tentar decodificar JSON se possível
                        try:
                            value = json.loads(value)
                        except Exception:
                            pass
                    info["value"] = value

                elif key_type == "hash":
                    hash_data = client.hgetall(key)
                    decoded_hash = {}
                    for k, v in hash_data.items():
                        k_decoded = k.decode('utf-8') if isinstance(
                            k,
                            bytes
                        ) else k
                        v_decoded = v.decode('utf-8') if isinstance(
                            v,
                            bytes
                        ) else v
                        try:
                            v_decoded = json.loads(v_decoded)
                        except Exception:
                            pass
                        decoded_hash[k_decoded] = v_decoded
                    info["value"] = decoded_hash
                    info["hash_length"] = len(decoded_hash)

                elif key_type == "list":
                    list_length = client.llen(key)
                    list_data = client.lrange(
                        key, 0, min(100, list_length - 1)
                    )  # Max 100 items
                    decoded_list = []
                    for item in list_data:
                        decoded_item = item.decode('utf-8') if isinstance(
                            item,
                            bytes
                        ) else item
                        try:
                            decoded_item = json.loads(decoded_item)
                        except Exception:
                            pass
                        decoded_list.append(decoded_item)
                    info["value"] = decoded_list
                    info["list_length"] = list_length
                    info["showing"] = len(decoded_list)

                elif key_type == "set":
                    set_data = client.smembers(key)
                    decoded_set = []
                    for item in set_data:
                        decoded_item = item.decode('utf-8') if isinstance(
                            item,
                            bytes
                        ) else item
                        try:
                            decoded_item = json.loads(decoded_item)
                        except Exception:
                            pass
                        decoded_set.append(decoded_item)
                    info["value"] = decoded_set
                    info["set_size"] = len(decoded_set)

                else:
                    info[
                        "value"
                    ] = f"Tipo '{key_type}' não suportado para visualização"

            except Exception as e:
                info["value_error"] = str(e)

            return info

        except Exception as e:
            logger.error(f"Error getting key info: {e}")
            return {"error": str(e)}

    def delete_key(self, key: str) -> bool:
        """
        Deleta uma chave do Redis.

        Parameters
        ----------
        key : str
            Nome da chave a deletar

        Returns
        -------
        bool
            True se deletada com sucesso
        """
        try:
            if self.redis_service.redis_client:
                result = self.redis_service.redis_client.delete(key)
                return result > 0
            return False
        except Exception as e:
            logger.error(f"Error deleting key: {e}")
            return False

    def get_embeddings_cache_keys(self) -> List[str]:
        """
        Obtém chaves específicas do cache de embeddings.

        Returns
        -------
        List[str]
            Lista de chaves de embeddings
        """
        try:
            # Buscar chaves que seguem o padrão do cache de embeddings
            embeddings_keys = self.get_all_keys("embeddings:*")
            search_keys = self.get_all_keys("search:*")
            cache_keys = self.get_all_keys("cache:*")

            all_keys = embeddings_keys + search_keys + cache_keys
            return sorted(set(all_keys))  # Remove duplicatas e ordena

        except Exception as e:
            logger.error(f"Error getting embeddings cache keys: {e}")
            return []

    def clear_cache(self, pattern: str = "*") -> int:
        """
        Limpa cache baseado em padrão.

        Parameters
        ----------
        pattern : str
            Padrão das chaves a limpar

        Returns
        -------
        int
            Número de chaves deletadas
        """
        try:
            if self.redis_service.redis_client:
                keys = self.get_all_keys(pattern)
                if keys:
                    return self.redis_service.redis_client.delete(*keys)
                return 0
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

    def render_health_status(self):
        """Renderiza o status de saúde do Redis."""
        st.subheader("🏥 Status de Saúde do Redis")

        with st.spinner("Verificando saúde do Redis..."):
            health_data = self.check_redis_health()

        if health_data["status"] == "healthy":
            st.success("✅ Redis está operacional")

            if "info" in health_data:
                info = health_data["info"]

                # Métricas principais
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    version = info.get("redis_version", "N/A")
                    st.metric("Versão do Redis", version)

                with col2:
                    connected_clients = info.get("connected_clients", "N/A")
                    st.metric("Clientes Conectados", connected_clients)

                with col3:
                    used_memory_human = info.get("used_memory_human", "N/A")
                    st.metric("Memória Usada", used_memory_human)

                with col4:
                    total_commands_processed = info.get(
                        "total_commands_processed", "N/A"
                    )
                    st.metric(
                        "Comandos Processados",
                        f"{total_commands_processed:,}" if isinstance(
                            total_commands_processed,
                            int
                        ) else total_commands_processed)

                # Informações detalhadas
                with st.expander("📊 Informações Detalhadas do Servidor"):
                    # Filtrar informações mais relevantes
                    relevant_info = {
                        "Servidor": {
                            "redis_version": info.get("redis_version"),
                            "redis_mode": info.get("redis_mode"),
                            "os": info.get("os"),
                            "uptime_in_seconds": info.get("uptime_in_seconds"),
                            "uptime_in_days": info.get("uptime_in_days")
                        },
                        "Memória": {
                            "used_memory_human": info.get("used_memory_human"),
                            "used_memory_peak_human": info.get(
                                "used_memory_peak_human"
                            ),
                            "total_system_memory_human": info.get(
                                "total_system_memory_human"
                            ),
                            "maxmemory_human": info.get("maxmemory_human")
                        },
                        "Clientes": {
                            "connected_clients": info.get("connected_clients"),
                            "client_longest_output_list": info.get(
                                "client_longest_output_list"
                            ),
                            "client_biggest_input_buf": info.get(
                                "client_biggest_input_buf"
                            )
                        },
                        "Estatísticas": {
                            "total_connections_received": info.get(
                                "total_connections_received"
                            ),
                            "total_commands_processed": info.get(
                                "total_commands_processed"
                            ),
                            "instantaneous_ops_per_sec": info.get(
                                "instantaneous_ops_per_sec"
                            ),
                            "keyspace_hits": info.get("keyspace_hits"),
                            "keyspace_misses": info.get("keyspace_misses")
                        }
                    }

                    for section, section_data in relevant_info.items():
                        st.markdown(f"**{section}:**")
                        for key, value in section_data.items():
                            if value is not None:
                                st.text(f"  {key}: {value}")
                        st.markdown("")

        elif health_data["status"] == "error":
            st.error(f"""❌ Erro no Redis: {
                health_data.get('error', 'Erro desconhecido')
            }""")

        else:
            st.error(
                f"""❌ Erro de conexão: {
                    health_data.get('error', 'Erro desconhecido')
                    }"""
                )

        st.caption(f"Última verificação: {health_data['timestamp']}")

    def render_keys_browser(self):
        """Renderiza navegador de chaves."""
        st.subheader("🔑 Navegador de Chaves")

        # Filtro de padrão
        col1, col2 = st.columns([3, 1])

        with col1:
            pattern = st.text_input(
                "Padrão de Busca",
                value="*",
                placeholder="ex: embeddings:*, cache:*, user:*",
            )

        with col2:
            if st.button("🔍 Buscar Chaves", type="primary"):
                st.rerun()

        # Buscar chaves
        with st.spinner("Buscando chaves..."):
            keys = self.get_all_keys(pattern)

        if keys:
            st.success(f"✅ {len(keys)} chave(s) encontrada(s)")

            # Estatísticas rápidas
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total de Chaves", len(keys))

            with col2:
                # Contar tipos de chaves por prefixo
                prefixes = {}
                for key in keys:
                    prefix = key.split(':')[0] if ':' in key else 'outros'
                    prefixes[prefix] = prefixes.get(prefix, 0) + 1
                most_common = max(
                    prefixes.items(),
                    key=lambda x: x[1]
                ) if prefixes else ("N/A", 0)
                st.metric(
                    "Prefixo Mais Comum",
                    f"{most_common[0]} ({most_common[1]})"
                )

            with col3:
                # Calcular tamanho médio das chaves (nome)
                avg_key_length = sum(len(key) for key in keys) / len(keys)
                st.metric("Tamanho Médio do Nome", f"{avg_key_length:.1f}")

            # Lista de chaves
            st.markdown("### 📋 Lista de Chaves")

            # Paginação simples
            keys_per_page = 20
            total_pages = (len(keys) + keys_per_page - 1) // keys_per_page

            if total_pages > 1:
                page = st.selectbox(
                    "Página",
                    range(1, total_pages + 1),
                    format_func=lambda x: f"Página {x} de {total_pages}"
                )
                start_idx = (page - 1) * keys_per_page
                end_idx = min(start_idx + keys_per_page, len(keys))
                display_keys = keys[start_idx:end_idx]
            else:
                display_keys = keys

            # Exibir chaves
            for key in display_keys:
                with st.expander(f"🔑 {key}"):
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        if st.button("👁️ Ver Detalhes", key=f"view_{key}"):
                            st.session_state[f"key_details_{key}"] = True

                    with col2:
                        if st.button(
                            "🗑️ Deletar",
                            key=f"delete_{key}",
                            type="secondary"
                        ):
                            if self.delete_key(key):
                                st.success(f"✅ Chave '{key}' deletada")
                                st.rerun()
                            else:
                                st.error(f"❌ Erro ao deletar '{key}'")

                    # Mostrar detalhes se solicitado
                    if st.session_state.get(f"key_details_{key}", False):
                        with st.spinner("Carregando detalhes..."):
                            key_info = self.get_key_info(key)

                        if "error" not in key_info:
                            st.markdown("**Informações:**")
                            st.text(f"Tipo: {key_info.get('type', 'N/A')}")
                            st.text(
                                f"TTL: {key_info.get('ttl', 'N/A')} segundos"
                            )
                            st.text(
                                f"""Memória: {key_info.get(
                                    'memory_usage', 'N/A')
                                } bytes"""
                            )

                            st.markdown("**Valor:**")
                            value = key_info.get("value", "N/A")

                            if isinstance(
                                value,
                                dict
                            ) or isinstance(value, list):
                                st.json(value)
                            else:
                                st.text(
                                    str(
                                        value
                                    )[
                                        :1000
                                    ] + ("..." if len(str(value)) > 1000 else (
                                        ""
                                    ))
                                )
                        else:
                            st.error(f"Erro: {key_info['error']}")

                        if st.button("❌ Fechar Detalhes", key=f"close_{key}"):
                            st.session_state[f"key_details_{key}"] = False
                            st.rerun()
        else:
            st.info("🔍 Nenhuma chave encontrada com o padrão especificado")

    def render_embeddings_cache(self):
        """Renderiza cache específico de embeddings."""
        st.subheader("🧠 Cache de Embeddings")

        with st.spinner("Carregando cache de embeddings..."):
            embeddings_keys = self.get_embeddings_cache_keys()

        if embeddings_keys:
            st.success(
                f"""✅ {
                    len(
                        embeddings_keys
                    )
                } entrada(s) de cache encontrada(s)""")

            # Opção de limpar cache
            col1, col2, col3 = st.columns([2, 1, 1])

            with col2:
                if st.button("🧹 Limpar Cache de Embeddings", type="secondary"):
                    cleared = self.clear_cache("embeddings:*")
                    cleared += self.clear_cache("search:*")
                    if cleared > 0:
                        st.success(
                            f"✅ {cleared} entrada(s) de cache removida(s)"
                        )
                        st.rerun()
                    else:
                        st.info("ℹ️ Nenhuma entrada para limpar")

            with col3:
                if st.button("🔄 Atualizar", type="primary"):
                    st.rerun()

            # Exibir entradas do cache
            st.markdown("### 📦 Entradas do Cache")

            for key in embeddings_keys[:10]:  # Limitar a 10 para performance
                with st.expander(f"💾 {key}"):
                    with st.spinner("Carregando..."):
                        key_info = self.get_key_info(key)

                    if "error" not in key_info:
                        # Informações básicas
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Tipo", key_info.get('type', 'N/A'))

                        with col2:
                            ttl = key_info.get('ttl', -1)
                            ttl_text = f"{ttl}s" if ttl > 0 else (
                                "Permanente"
                            ) if ttl == -1 else "Expirada"
                            st.metric("TTL", ttl_text)

                        with col3:
                            memory = key_info.get('memory_usage', 'N/A')
                            memory_text = f"{memory}B" if isinstance(
                                memory,
                                int
                            ) else str(memory)
                            st.metric("Memória", memory_text)

                        # Valor do cache
                        value = key_info.get("value")
                        if value:
                            st.markdown("**Conteúdo do Cache:**")

                            if isinstance(value, dict):
                                # Se é um cache de embeddings estruturado
                                if "similar_texts" in value:
                                    similar_texts = value["similar_texts"]
                                    st.info(
                                        f"""📊 Cache contém {
                                            len(similar_texts)
                                        } texto(s) similar(es)"""
                                    )

                                    for i, (
                                        text_data,
                                        score
                                    ) in enumerate(similar_texts[:3], 1):
                                        st.markdown(
                                            f"""**{i}.** {
                                                text_data.get(
                                                    'title',
                                                    'Sem título'
                                                )
                                            } (Score: {score:.3f})"""
                                        )

                                    if len(similar_texts) > 3:
                                        st.caption(
                                            f"""... e mais {
                                                len(similar_texts) - 3
                                            } texto(s)"""
                                        )

                                # JSON expandido
                                with st.expander("🔍 JSON Completo"):
                                    st.json(value)
                            else:
                                # Texto simples
                                value_str = str(value)
                                if len(value_str) > 500:
                                    st.text(value_str[:500] + "...")
                                else:
                                    st.text(value_str)
                        else:
                            st.info("Cache vazio")

                        # Botão para deletar entrada específica
                        if st.button(
                            "🗑️ Remover Esta Entrada",
                            key=f"del_cache_{key}"
                        ):
                            if self.delete_key(key):
                                st.success(f"✅ Cache '{key}' removido")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao remover cache")

                    else:
                        st.error(f"Erro ao carregar: {key_info['error']}")

            if len(embeddings_keys) > 10:
                st.info(
                    f"""Mostrando 10 de {
                        len(embeddings_keys)
                    } entradas. Use o navegador de chaves para ver todas."""
                )

        else:
            st.info("🔍 Nenhum cache de embeddings encontrado")

    def render_cache_management(self):
        """Renderiza interface de gerenciamento de cache."""
        st.subheader("🔧 Gerenciamento de Cache")

        st.markdown("""
        Esta seção permite limpar diferentes tipos de cache no Redis.
        **⚠️ Atenção: Esta ação é irreversível!**
        """)

        # Opções de limpeza
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🧹 Limpeza Seletiva")

            cache_options = {
                "embeddings:*": "Cache de Embeddings",
                "search:*": "Cache de Buscas",
                "cache:*": "Cache Geral",
                "session:*": "Sessões de Usuário",
                "*": "⚠️ TODOS OS DADOS"
            }

            selected_pattern = st.selectbox(
                "Selecione o que limpar:",
                list(cache_options.keys()),
                format_func=lambda x: cache_options[x]
            )

            # Preview das chaves que serão afetadas
            if selected_pattern != "*":
                preview_keys = self.get_all_keys(selected_pattern)
                st.info(f"📋 {len(preview_keys)} chave(s) serão afetadas")

                if preview_keys and len(preview_keys) <= 20:
                    with st.expander("👁️ Preview das Chaves"):
                        for key in preview_keys:
                            st.text(f"• {key}")
                elif len(preview_keys) > 20:
                    with st.expander("👁️ Preview (primeiras 20)"):
                        for key in preview_keys[:20]:
                            st.text(f"• {key}")
                        st.caption(
                            f"... e mais {len(preview_keys) - 20} chave(s)"
                        )

            # Confirmação
            confirm_text = st.text_input(
                f"""Digite 'CONFIRMAR' para limpar {
                    cache_options[selected_pattern]
                }:""",
                placeholder="CONFIRMAR"
            )

            if st.button(
                f"🗑️ Limpar {cache_options[selected_pattern]}",
                type="secondary"
            ):
                if confirm_text == "CONFIRMAR":
                    with st.spinner("Limpando cache..."):
                        cleared = self.clear_cache(selected_pattern)

                    if cleared > 0:
                        st.success(
                            f"✅ {cleared} entrada(s) de cache removida(s)"
                        )
                    else:
                        st.info("ℹ️ Nenhuma entrada encontrada para limpar")
                else:
                    st.error("❌ Digite 'CONFIRMAR' para prosseguir")

        with col2:
            st.markdown("### 📊 Estatísticas do Cache")

            # Estatísticas por tipo de cache
            cache_stats = {}

            for pattern, name in cache_options.items():
                if pattern != "*":
                    keys = self.get_all_keys(pattern)
                    cache_stats[name] = len(keys)

            if cache_stats:
                # Gráfico simples com métricas
                for cache_type, count in cache_stats.items():
                    st.metric(cache_type, count)

                # Informação adicional
                total_keys = sum(cache_stats.values())
                st.markdown(f"**Total de Chaves de Cache:** {total_keys}")

            else:
                st.info("📊 Nenhum dado de cache encontrado")

    def render_main_interface(self):
        """Renderiza interface principal do monitor."""
        st.title("📊 Monitor do Redis")
        st.markdown("Ferramenta para monitoramento e consulta do Redis")

        # Tabs para diferentes funcionalidades
        tab1, tab2, tab3, tab4 = st.tabs([
            "🏥 Saúde",
            "🔑 Navegador",
            "🧠 Embeddings",
            "🔧 Gerenciar"
        ])

        with tab1:
            self.render_health_status()

        with tab2:
            self.render_keys_browser()

        with tab3:
            self.render_embeddings_cache()

        with tab4:
            self.render_cache_management()
