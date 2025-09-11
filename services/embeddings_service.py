import requests
import os
import numpy as np
from typing import List, Dict, Tuple, Optional
from dictionary.vars import API_BASE_URL
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Serviço para consultar embeddings via API do Django existente.
    Usa os embeddings já armazenados no banco de dados da API.
    """

    def __init__(self):
        """
        Inicializa o serviço de embeddings usando a API do Django existente.
        """
        self.api_base_url = API_BASE_URL or os.getenv('DJANGO_API_URL')

        if not self.api_base_url:
            logger.warning("API_BASE_URL not configured")

    def get_all_embeddings(self, limit: int = 100) -> List[Dict]:
        """
        Obtém todos os embeddings disponíveis na API.

        Parameters
        ----------
        limit : int
            Número máximo de resultados

        Returns
        -------
        List[Dict]
            Lista de embeddings da API
        """
        try:
            if not self.api_base_url:
                logger.error("API not configured")
                return []

            headers = {
                'Content-Type': 'application/json'
            }

            # Usar endpoint real da API
            response = requests.get(
                f"{self.api_base_url}/embeddings/",
                headers=headers,
                params={'limit': limit},
                timeout=30
            )

            if response.status_code == 200:
                results = response.json()
                logger.info(f"Retrieved {len(results)} embeddings from API")
                return results
            else:
                logger.error(f"API error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error retrieving embeddings from API: {e}")
            return []

    def search_texts(
        self, 
        query: str,
        size: int = 20,
        filters: Optional[Dict] = None,
        search_fields: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Busca textos similares com filtros avançados.

        Parameters
        ----------
        query : str
            Consulta de busca
        size : int
            Número máximo de resultados
        filters : Dict, optional
            Filtros adicionais (ex: {'platform': 'Facebook', 'origin': 'social'})
        search_fields : List[str], optional
            Campos específicos para busca (ex: ['title', 'content', 'theme'])

        Returns
        -------
        List[Dict]
            Lista de textos similares encontrados
        """
        try:
            # Obter todos os embeddings disponíveis
            all_embeddings = self.get_all_embeddings()

            if not all_embeddings:
                logger.warning("No embeddings found in API")
                return []

            # Configurar campos de busca padrão
            if search_fields is None:
                search_fields = ['title', 'content', 'theme']
            
            # Configurar filtros padrão
            if filters is None:
                filters = {}

            similar_texts = []
            query_lower = query.lower()

            for embedding_data in all_embeddings:
                # Aplicar filtros primeiro
                if not self._apply_filters(embedding_data, filters):
                    continue

                # Calcular score de similaridade
                score = self._calculate_text_similarity(
                    embedding_data, query_lower, search_fields
                )

                if score > 0:
                    formatted_item = self._format_search_result(
                        embedding_data, score
                    )
                    similar_texts.append(formatted_item)

            # Ordenar por score e limitar resultados
            similar_texts.sort(key=lambda x: x['score'], reverse=True)
            result = similar_texts[:size]

            logger.info(f"Found {len(result)} similar texts via text matching")
            return result

        except Exception as e:
            logger.error(f"Error searching texts: {e}")
            return []

    def calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calcula similaridade cosseno entre dois vetores.

        Parameters
        ----------
        vec1 : List[float]
            Primeiro vetor
        vec2 : List[float]
            Segundo vetor

        Returns
        -------
        float
            Similaridade cosseno (0-1)
        """
        try:
            vec1 = np.array(vec1)  # type: ignore
            vec2 = np.array(vec2)  # type: ignore

            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)

            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0.0

            return float(dot_product / (norm_vec1 * norm_vec2))
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    def find_similar_texts(
        self,
        query_text: str,
        candidate_texts: List[Dict],
        top_k: int = 10
    ) -> List[Tuple[Dict, float]]:
        """
        Encontra textos similares usando busca textual simples.
        Em um ambiente real, usaria embeddings para cálculo de similaridade.

        Parameters
        ----------
        query_text : str
            Texto de consulta
        candidate_texts : List[Dict]
            Lista de textos candidatos
        top_k : int
            Número de resultados mais similares

        Returns
        -------
        List[Tuple[Dict, float]]
            Lista de (texto, score de similaridade)
        """
        try:
            query_lower = query_text.lower()
            similarities = []

            for text_data in candidate_texts:
                content = text_data.get('text', '').lower()
                title = text_data.get('title', '').lower()

                # Cálculo de similaridade baseado em correspondência textual
                score = 0.0

                # Palavras em comum
                query_words = set(query_lower.split())
                content_words = set(content.split())
                title_words = set(title.split())

                content_intersection = len(query_words.intersection(content_words))
                title_intersection = len(query_words.intersection(title_words))

                if content_intersection > 0:
                    score += (content_intersection / len(query_words)) * 0.7

                if title_intersection > 0:
                    score += (title_intersection / len(query_words)) * 0.9

                # Substring matches
                if query_lower in content:
                    score += 0.5
                if query_lower in title:
                    score += 0.7

                if score > 0.1:  # Threshold mínimo
                    similarities.append((text_data, score))

            # Ordenar por similaridade
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Filtrar resultados com score muito baixo
            filtered_similarities = [
                (text, score) for text, score in similarities
                if score >= 0.2
            ]

            result = filtered_similarities[:top_k]
            logger.info(f"Found {len(result)} similar texts via text matching")
            return result

        except Exception as e:
            logger.error(f"Error finding similar texts: {e}")
            return []

    def is_configured(self) -> bool:
        """
        Verifica se a API está configurada.

        Returns
        -------
        bool
            True se configurada, False caso contrário
        """
        return bool(self.api_base_url)

    def health_check(self) -> bool:
        """
        Verifica se a API está funcionando.

        Returns
        -------
        bool
            True se API está respondendo, False caso contrário
        """
        try:
            if not self.is_configured():
                return False

            headers = {
                'Content-Type': 'application/json'
            }

            # Testar endpoint real da API
            response = requests.get(
                f"{self.api_base_url}/embeddings/",
                headers=headers,
                params={'limit': 1},
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_embeddings_stats(self, token: str) -> Dict:
        """
        Obtém estatísticas dos embeddings com autenticação.

        Parameters
        ----------
        token : str, optional
            Token de autenticação

        Returns
        -------
        Dict
            Estatísticas dos embeddings
        """
        try:
            headers = {
                'Content-Type': 'application/json'
            }

            if token:
                headers['Authorization'] = f'Bearer {token}'

            response = requests.get(
                f"{self.api_base_url}/embeddings/",
                headers=headers,
                params={'limit': 100},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                embeddings = data.get(
                    'results',
                    data
                ) if isinstance(data, dict) else data

                stats = {
                    'total': len(embeddings),
                    'origins': {},
                    'with_title': 0,
                    'without_title': 0,
                    'avg_content_length': 0
                }

                if embeddings:
                    total_length = 0
                    for emb in embeddings:
                        origin = emb.get('origin', 'unknown')
                        stats['origins'][origin] = stats['origins'].get(origin, 0) + 1

                        if emb.get('title'):
                            stats['with_title'] += 1
                        else:
                            stats['without_title'] += 1

                        content = emb.get('content', '')
                        total_length += len(content)

                    stats['avg_content_length'] = int(total_length / len(embeddings))

                return stats
            else:
                return {'error': f'HTTP {response.status_code}'}

        except Exception as e:
            logger.error(f"Error getting embeddings stats: {e}")
            return {'error': str(e)}

    def _apply_filters(self, embedding_data: Dict, filters: Dict) -> bool:
        """
        Aplica filtros aos dados do embedding.

        Parameters
        ----------
        embedding_data : Dict
            Dados do embedding
        filters : Dict
            Filtros a serem aplicados

        Returns
        -------
        bool
            True se passa pelos filtros, False caso contrário
        """
        try:
            metadata = embedding_data.get('metadata', {})

            # Filtro por plataforma
            if 'platform' in filters:
                platform_display = metadata.get('platform_display', '').lower()
                if filters['platform'].lower() not in platform_display:
                    return False

            # Filtro por origem
            if 'origin' in filters:
                origin = embedding_data.get('origin', '').lower()
                if filters['origin'].lower() not in origin:
                    return False

            # Filtro por tema
            if 'theme' in filters:
                theme = metadata.get('theme', '').lower()
                if filters['theme'].lower() not in theme:
                    return False

            # Filtro por data (se fornecida)
            if 'created_after' in filters:
                created_at = embedding_data.get('created_at', '')
                if created_at < filters['created_after']:
                    return False

            if 'created_before' in filters:
                created_at = embedding_data.get('created_at', '')
                if created_at > filters['created_before']:
                    return False

            # Filtro por ID específico
            if 'id' in filters:
                if str(embedding_data.get('id', '')) != str(filters['id']):
                    return False

            return True

        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return True  # Em caso de erro, não filtra

    def _calculate_text_similarity(
        self,
        embedding_data: Dict,
        query_lower: str,
        search_fields: List[str]
    ) -> float:
        """
        Calcula similaridade textual baseada nos campos especificados.

        Parameters
        ----------
        embedding_data : Dict
            Dados do embedding
        query_lower : str
            Query em lowercase
        search_fields : List[str]
            Campos para buscar

        Returns
        -------
        float
            Score de similaridade
        """
        try:
            score = 0.0
            content = embedding_data.get('content', '').lower()
            title = embedding_data.get('title', '').lower()
            metadata = embedding_data.get('metadata', {})
            theme = metadata.get('theme', '').lower()

            # Pesos para diferentes campos
            field_weights = {
                'title': 0.9,
                'content': 0.8,
                'theme': 0.7
            }

            for field in search_fields:
                field_weight = field_weights.get(field, 0.5)

                if field == 'title' and title:
                    if query_lower in title:
                        score += field_weight
                    # Bonus para correspondência de palavras
                    query_words = set(query_lower.split())
                    title_words = set(title.split())
                    word_match_ratio = len(
                        query_words.intersection(title_words)
                    ) / len(query_words) if query_words else 0
                    score += word_match_ratio * field_weight * 0.7

                elif field == 'content' and content:
                    if query_lower in content:
                        score += field_weight
                    # Bonus para correspondência de palavras
                    query_words = set(query_lower.split())
                    content_words = set(content.split())
                    word_match_ratio = len(
                        query_words.intersection(content_words)
                    ) / len(query_words) if query_words else 0
                    score += word_match_ratio * field_weight * 0.5

                elif field == 'theme' and theme:
                    if query_lower in theme:
                        score += field_weight
                    # Bonus para correspondência de palavras
                    query_words = set(query_lower.split())
                    theme_words = set(theme.split())
                    word_match_ratio = len(
                        query_words.intersection(theme_words)
                    ) / len(query_words) if query_words else 0
                    score += word_match_ratio * field_weight * 0.8

            return min(score, 2.0)  # Limitar score máximo

        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return 0.0

    def _format_search_result(
        self,
        embedding_data: Dict,
        score: float
    ) -> Dict:
        """
        Formata resultado de busca para exibição.

        Parameters
        ----------
        embedding_data : Dict
            Dados do embedding
        score : float
            Score de similaridade

        Returns
        -------
        Dict
            Resultado formatado
        """
        try:
            metadata = embedding_data.get('metadata', {})

            return {
                'id': embedding_data.get('id', ''),
                'title': embedding_data.get('title', ''),
                'content': embedding_data.get('content', ''),
                'score': round(score, 3),
                'type': 'Post Gerado',
                'author': metadata.get('platform_display', 'Sistema'),
                'created_at': embedding_data.get('created_at', ''),
                'origin': embedding_data.get('origin', ''),
                'theme': metadata.get('theme', ''),
                'platform': metadata.get('platform_display', ''),
                'index': 'generated_posts',
                'metadata': metadata
            }

        except Exception as e:
            logger.error(f"Error formatting search result: {e}")
            return {
                'id': embedding_data.get('id', ''),
                'title': embedding_data.get('title', ''),
                'content': embedding_data.get('content', ''),
                'score': score,
                'type': 'Post Gerado',
                'error': f'Format error: {str(e)}'
            }

    def check_api_health(self, token: str) -> Dict:
        """
        Verifica a saúde da API de embeddings.

        Parameters
        ----------
        token : str, optional
            Token de autenticação

        Returns
        -------
        Dict
            Status da API
        """
        try:
            headers = {
                'Content-Type': 'application/json'
            }

            if token:
                headers['Authorization'] = f'Bearer {token}'

            response = requests.get(
                f"{self.api_base_url}/embeddings/",
                headers=headers,
                params={'limit': 1},
                timeout=5
            )

            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'message': 'API respondendo normalmente',
                    'authenticated': True
                }
            elif response.status_code == 401:
                return {
                    'status': 'healthy',
                    'message': 'API respondendo (autenticação necessária)',
                    'authenticated': False
                }
            else:
                return {
                    'status': 'error',
                    'message': f'API retornou status {response.status_code}',
                    'authenticated': False
                }

        except requests.exceptions.ConnectionError:
            return {
                'status': 'error',
                'message': 'Não foi possível conectar com a API',
                'authenticated': False
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Erro: {str(e)}',
                'authenticated': False
            }

    def search_by_theme(self, theme: str, size: int = 10) -> List[Dict]:
        """
        Busca embeddings por tema específico.

        Parameters
        ----------
        theme : str
            Tema para buscar
        size : int
            Número máximo de resultados

        Returns
        -------
        List[Dict]
            Lista de embeddings encontrados
        """
        filters = {'theme': theme}
        return self.search_texts(
            query=theme,
            size=size,
            filters=filters,
            search_fields=['theme', 'title', 'content']
        )

    def search_by_platform(
        self,
        platform: str,
        query: str = "",
        size: int = 10
    ) -> List[Dict]:
        """
        Busca embeddings por plataforma específica.

        Parameters
        ----------
        platform : str
            Plataforma para filtrar (Facebook, Instagram, etc.)
        query : str, optional
            Consulta adicional de busca
        size : int
            Número máximo de resultados

        Returns
        -------
        List[Dict]
            Lista de embeddings encontrados
        """
        filters = {'platform': platform}
        search_query = query if query else platform

        return self.search_texts(
            query=search_query, 
            size=size, 
            filters=filters,
            search_fields=['title', 'content', 'theme']
        )

    def get_available_themes(self, limit: int = 100) -> List[str]:
        """
        Obtém lista de temas disponíveis nos embeddings.

        Parameters
        ----------
        limit : int
            Limite de embeddings para analisar

        Returns
        -------
        List[str]
            Lista de temas únicos encontrados
        """
        try:
            all_embeddings = self.get_all_embeddings(limit=limit)
            themes = set()

            for embedding in all_embeddings:
                metadata = embedding.get('metadata', {})
                theme = metadata.get('theme', '').strip()
                if theme:
                    themes.add(theme)

            return sorted(list(themes))

        except Exception as e:
            logger.error(f"Error getting available themes: {e}")
            return []

    def get_available_platforms(self, limit: int = 100) -> List[str]:
        """
        Obtém lista de plataformas disponíveis nos embeddings.

        Parameters
        ----------
        limit : int
            Limite de embeddings para analisar

        Returns
        -------
        List[str]
            Lista de plataformas únicas encontradas
        """
        try:
            all_embeddings = self.get_all_embeddings(limit=limit)
            platforms = set()

            for embedding in all_embeddings:
                metadata = embedding.get('metadata', {})
                platform = metadata.get('platform_display', '').strip()
                if platform:
                    platforms.add(platform)

            return sorted(list(platforms))

        except Exception as e:
            logger.error(f"Error getting available platforms: {e}")
            return []

    def get_recent_embeddings(
        self,
        days: int = 7,
        size: int = 20
    ) -> List[Dict]:
        """
        Obtém embeddings recentes baseado em número de dias.

        Parameters
        ----------
        days : int
            Número de dias para buscar embeddings recentes
        size : int
            Número máximo de resultados

        Returns
        -------
        List[Dict]
            Lista de embeddings recentes
        """
        try:
            from datetime import datetime, timedelta

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            filters = {'created_after': cutoff_date}

            return self.search_texts(
                query="",
                size=size,
                filters=filters,
                search_fields=['title', 'content']
            )

        except Exception as e:
            logger.error(f"Error getting recent embeddings: {e}")
            return []

    def search_all_embeddings_like(
        self, 
        search_text: str,
        size: int = 20
    ) -> List[Dict]:
        """
        Busca TODOS os embeddings que contenham o texto especificado em qualquer campo.
        Funciona como SELECT * FROM embeddings_embedding WHERE content LIKE '%search_text%'.

        Parameters
        ----------
        search_text : str
            Texto a ser procurado em todas as colunas
        size : int
            Número máximo de resultados

        Returns
        -------
        List[Dict]
            Lista completa de todos os campos dos embeddings que contêm o texto
        """
        try:
            # Obter todos os embeddings da API
            all_embeddings = self.get_all_embeddings(limit=1000)  # Buscar mais registros
            
            if not all_embeddings:
                logger.warning("No embeddings found in API")
                return []

            search_lower = search_text.lower() if search_text else ""
            matching_embeddings = []

            for embedding in all_embeddings:
                # Se não há texto de busca, retornar todos
                if not search_text or not search_text.strip():
                    matching_embeddings.append(embedding)
                    continue
                
                # Buscar em todas as possíveis colunas/campos do embedding
                found_match = False
                
                # Campos principais
                fields_to_search = [
                    embedding.get('id', ''),
                    embedding.get('title', ''),
                    embedding.get('content', ''),
                    embedding.get('origin', ''),
                    embedding.get('created_at', ''),
                    embedding.get('updated_at', ''),
                    str(embedding.get('vector_dimension', '')),
                ]
                
                # Campos de metadata
                metadata = embedding.get('metadata', {})
                if isinstance(metadata, dict):
                    fields_to_search.extend([
                        metadata.get('theme', ''),
                        metadata.get('platform_display', ''),
                        metadata.get('platform', ''),
                        metadata.get('author', ''),
                        metadata.get('tags', ''),
                        str(metadata.get('length', '')),
                        str(metadata.get('word_count', '')),
                    ])
                
                # Buscar o texto em todos os campos
                for field_value in fields_to_search:
                    if isinstance(field_value, str) and search_lower in field_value.lower():
                        found_match = True
                        break
                    elif not isinstance(field_value, str) and search_lower in str(field_value).lower():
                        found_match = True
                        break
                
                if found_match:
                    matching_embeddings.append(embedding)
            
            # Limitar resultados e retornar
            result = matching_embeddings[:size]
            
            logger.info(f"Found {len(result)} embeddings matching '{search_text}'")
            return result

        except Exception as e:
            logger.error(f"Error in search_all_embeddings_like: {e}")
            return []

    def advanced_search(
        self,
        query: str,
        theme: str,
        platform: str,
        origin: str,
        created_after: str,
        created_before: str,
        search_fields: List[str],
        size: int = 20
    ) -> List[Dict]:
        """
        Busca avançada com múltiplos filtros combinados.

        Parameters
        ----------
        query : str
            Consulta de busca textual
        theme : str, optional
            Filtrar por tema
        platform : str, optional
            Filtrar por plataforma
        origin : str, optional
            Filtrar por origem
        created_after : str, optional
            Filtrar por data de criação (após)
        created_before : str, optional
            Filtrar por data de criação (antes)
        search_fields : List[str], optional
            Campos específicos para buscar
        size : int
            Número máximo de resultados

        Returns
        -------
        List[Dict]
            Lista de embeddings encontrados
        """
        try:
            filters = {}

            if theme:
                filters['theme'] = theme
            if platform:
                filters['platform'] = platform
            if origin:
                filters['origin'] = origin
            if created_after:
                filters['created_after'] = created_after
            if created_before:
                filters['created_before'] = created_before

            # Se não há query, usar um termo genérico para ativar a busca
            search_query = query if query.strip() else "conteúdo"

            return self.search_texts(
                query=search_query,
                size=size,
                filters=filters,
                search_fields=search_fields
            )

        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return []
