import requests
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from services.redis_service import RedisService
from dictionary.vars import API_BASE_URL
import logging

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Serviço para consulta de embeddings via API.
    Responsável pela busca de textos similares através da API de embeddings.
    """

    def __init__(self):
        """
        Inicializa o serviço de embeddings.
        """
        self.api_base_url = API_BASE_URL
        try:
            self.redis_service = RedisService()
            self.redis_client = self.redis_service.client if hasattr(
                self.redis_service,
                'client'
            ) else None
        except Exception as e:
            logger.warning(f"Redis service not available: {e}")
            self.redis_service = None
            self.redis_client = None

        self.username = "johndoe"
        self.password = "orrARDrdr27!"
        self.auth_token = None

        logger.info("EmbeddingsService initialized")

    def authenticate(self) -> bool:
        """
        Autentica na API para obter token de acesso.

        Returns
        -------
        bool
            True se autenticado com sucesso, False caso contrário
        """
        try:
            auth_url = f"{self.api_base_url}/authentication/token/"
            auth_data = {
                "username": self.username,
                "password": self.password
            }

            response = requests.post(auth_url, json=auth_data, timeout=10)

            if response.status_code == 200:
                token_data = response.json()
                self.auth_token = token_data.get("access")
                logger.info("Authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """
        Retorna headers com token de autenticação.

        Returns
        -------
        Dict[str, str]
            Headers com autorização
        """
        if not self.auth_token:
            self.authenticate()

        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }

    def fetch_embeddings(
        self,
        origin: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca embeddings da API com filtros opcionais.

        Parameters
        ----------
        origin : Optional[str]
            Filtro por origem (webscraping, generated, business_brain)
        search_query : Optional[str]
            Query para busca em título e conteúdo

        Returns
        -------
        List[Dict]
            Lista de embeddings encontrados
        """
        try:
            embeddings_url = f"{self.api_base_url}/embeddings/"
            headers = self.get_headers()

            params = {}
            if origin:
                params["origin"] = origin
            if search_query:
                params["search"] = search_query

            response = requests.get(
                embeddings_url,
                headers=headers,
                params=params,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                # A API retorna um formato simples com lista de embeddings
                if isinstance(data, list):
                    logger.info(f"Fetched {len(data)} embeddings from API")
                    return data
                elif isinstance(data, dict):
                    # Se retornar um dict com chave 'results' (paginação)
                    if "results" in data:
                        embeddings = data["results"]
                        logger.info(
                            f"Fetched {len(embeddings)} embeddings from API"
                        )
                        return embeddings
                    # Se retornar dict com metadados (formato especial)
                    elif "metadados" in data:
                        embeddings = data["metadados"]
                        logger.info(
                            f"Fetched {len(embeddings)} embeddings from API"
                        )
                        return embeddings
                    else:
                        logger.warning(
                            f"Unexpected API response format: {data}")
                        return []
                else:
                    logger.warning(f"Unexpected data type: {type(data)}")
                    return []

            elif response.status_code == 401:
                # Token expirado, tentar re-autenticar
                logger.warning("Token expired, re-authenticating...")
                if self.authenticate():
                    return self.fetch_embeddings(search_query=search_query)
                else:
                    logger.error("Re-authentication failed")
                    return []
            else:
                logger.error(
                    f"Error fetching embeddings: {response.status_code}"
                )
                return []

        except Exception as e:
            logger.error(f"Error fetching embeddings: {e}")
            return []

    def query_embeddings_by_individual_words(
        self,
        query_text: str
    ) -> Dict[str, List[Dict]]:
        """
        Consulta embeddings por palavras individuais do texto.
        
        Parameters
        ----------
        query_text : str
            Texto para dividir em palavras e buscar individualmente
            
        Returns
        -------
        Dict[str, List[Dict]]
            Dicionário com cada palavra como chave e lista de embeddings como valor
        """
        try:
            # Dividir texto em palavras (remover pontuação e espaços)
            import re
            words = re.findall(r'\b[a-záàâãéèêíìîóòôõúùûç]+\b', query_text.lower())
            
            # Remover palavras muito curtas (menos de 3 caracteres)
            words = [word for word in words if len(word) >= 3]
            
            # Remover duplicatas mantendo ordem
            words = list(dict.fromkeys(words))
            
            results_by_word = {}
            
            for word in words:
                # Verificar cache primeiro para esta palavra
                cached_embeddings = None
                if self.redis_service:
                    try:
                        cached_embeddings = self.redis_service.get_cached_embeddings_by_word(word)
                    except Exception as e:
                        logger.warning(f"Error accessing Redis cache for word '{word}': {e}")
                
                if cached_embeddings:
                    results_by_word[word] = cached_embeddings
                    logger.info(f"Using cached embeddings for word: {word}")
                else:
                    # Consultar embeddings para cada palavra individual
                    word_embeddings = self.query_embeddings_by_text(word)
                    if word_embeddings:
                        results_by_word[word] = word_embeddings
                        
                        # Cache os resultados da palavra individual
                        if self.redis_service:
                            try:
                                self.redis_service.cache_embeddings_by_word(word, word_embeddings)
                            except Exception as e:
                                logger.warning(f"Error caching embeddings for word '{word}': {e}")
                    
            logger.info(f"Consulted {len(words)} individual words, found results for {len(results_by_word)} words")
            return results_by_word
            
        except Exception as e:
            logger.error(f"Error querying embeddings by individual words: {e}")
            return {}

    def query_embeddings_by_text(
        self,
        query_text: str
    ) -> List[Dict]:
        """
        Consulta embeddings por texto, buscando similares em todas as origens.

        Parameters
        ----------
        query_text : str
            Texto para busca de similares
        top_k : int
            Número de resultados mais similares

        Returns
        -------
        List[Dict]
            Lista de embeddings similares ordenados por relevância
        """
        try:
            # Verificar cache primeiro (se Redis disponível)
            cached_result = None
            if self.redis_service:
                try:
                    cached_result = self.redis_service.get_cached_embeddings(
                        query_text
                    )
                except Exception as e:
                    logger.warning(f"Error accessing Redis cache: {e}")

            if cached_result and isinstance(cached_result, dict):
                similar_texts = cached_result.get("similar_texts", [])
                if similar_texts:
                    logger.info(
                        f"Found {len(similar_texts)} cached embeddings"
                    )
                    return [text_data for text_data, _ in similar_texts]

            # Buscar na API - buscar em todas as origens usando o query
            embeddings = self.fetch_embeddings(search_query=query_text)
            if not embeddings:
                logger.warning("No embeddings found in API")
                return []

            query_lower = query_text.lower()
            query_words = query_lower.split()

            for embedding in embeddings:
                content = embedding.get("content", "").lower()
                title = embedding.get("title", "").lower()

                # Calcular score baseado em matches de palavras-chave
                content_matches = sum(
                    1 for word in query_words if word in content
                )
                title_matches = sum(1 for word in query_words if word in title)

                # Score com peso maior para matches no título
                score = (title_matches * 2 + content_matches) / len(
                    query_words
                )
                embedding["similarity_score"] = max(score, 0.1)

            # Ordenar por score de similaridade
            embeddings.sort(
                key=lambda x: x.get("similarity_score", 0),
                reverse=True
            )

            results = embeddings
            # Cache do resultado (se Redis disponível)
            if self.redis_service:
                try:
                    cache_data = {
                        "similar_texts": [
                            (
                                emb,
                                emb.get("similarity_score", 0)
                            ) for emb in results
                        ],
                        "query": query_text,
                        "total_found": len(embeddings)
                    }
                    self.redis_service.cache_embeddings(query_text, cache_data)
                except Exception as e:
                    logger.warning(f"Error caching results: {e}")

            logger.info(f"Found {len(results)} similar embeddings for query")
            return results

        except Exception as e:
            logger.error(f"Error querying embeddings by text: {e}")
            return []

    def calculate_cosine_similarity(
        self,
        vector_a: List[float],
        vector_b: List[float]
    ) -> float:
        """
        Calcula similaridade cosseno entre dois vetores.

        Parameters
        ----------
        vector_a : List[float]
            Primeiro vetor
        vector_b : List[float]
            Segundo vetor

        Returns
        -------
        float
            Score de similaridade entre 0 e 1
        """
        try:
            if not vector_a or not vector_b or len(vector_a) != len(vector_b):
                return 0.0

            a = np.array(vector_a)
            b = np.array(vector_b)

            # Calcular produto escalar
            dot_product = np.dot(a, b)

            # Calcular normas
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            # Evitar divisão por zero
            if norm_a == 0 or norm_b == 0:
                return 0.0

            # Calcular similaridade cosseno
            similarity = dot_product / (norm_a * norm_b)

            # Normalizar para [0, 1]
            return max(0.0, min(1.0, (similarity + 1) / 2))

        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    def find_similar_texts(
        self,
        user_input: str,
        candidate_texts: List[Dict],
    ) -> List[Tuple[Dict, float]]:
        """
        Encontra textos similares ao input do usuário.

        Parameters
        ----------
        user_input : str
            Input do usuário
        candidate_texts : List[Dict]
            Lista de textos candidatos
        top_k : int
            Número de resultados mais similares

        Returns
        -------
        List[Tuple[Dict, float]]
            Lista de (dados do texto, score de similaridade)
        """
        try:
            # Se não há textos candidatos, buscar na API
            if not candidate_texts:
                similar_embeddings = self.query_embeddings_by_text(
                    user_input
                )
                return [
                    (
                        emb,
                        emb.get("similarity_score", 0.5)
                    ) for emb in similar_embeddings
                ]

            # Calcular similaridade com textos candidatos
            similar_texts = []
            user_input_lower = user_input.lower()
            user_words = set(user_input_lower.split())

            for text_data in candidate_texts:
                content = text_data.get("content", "").lower()
                title = text_data.get("title", "").lower()

                # Calcular similaridade baseada em palavras comuns
                content_words = set(content.split())
                title_words = set(title.split())
                all_text_words = content_words.union(title_words)

                # Jaccard similarity
                intersection = len(user_words.intersection(all_text_words))
                union = len(user_words.union(all_text_words))

                if union > 0:
                    jaccard_similarity = intersection / union

                    # Boost se há match no título
                    title_boost = 0.3 if any(
                        word in title for word in user_words
                    ) else 0

                    final_score = min(1.0, jaccard_similarity + title_boost)
                    similar_texts.append((text_data, final_score))

            # Ordenar por score
            similar_texts.sort(key=lambda x: x[1], reverse=True)

            results = similar_texts
            logger.info(f"Found {len(results)} similar texts from candidates")
            return results

        except Exception as e:
            logger.error(f"Error finding similar texts: {e}")
            return []

    def get_embedding_by_id(self, embedding_id: str) -> Optional[Dict]:
        """
        Busca um embedding específico por ID.

        Parameters
        ----------
        embedding_id : str
            ID do embedding

        Returns
        -------
        Optional[Dict]
            Dados do embedding ou None se não encontrado
        """
        try:
            embedding_url = f"{self.api_base_url}/embeddings/{embedding_id}/"
            headers = self.get_headers()

            response = requests.get(embedding_url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Fetched embedding {embedding_id}")
                return data
            elif response.status_code == 401:
                # Token expirado
                if self.authenticate():
                    return self.get_embedding_by_id(embedding_id)
                else:
                    return None
            else:
                logger.error(
                    f"""Error fetching embedding {
                        embedding_id}
                    : {
                        response.status_code
                    }"""
                )
                return None

        except Exception as e:
            logger.error(f"Error fetching embedding by ID: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas dos embeddings.

        Returns
        -------
        Dict[str, Any]
            Estatísticas dos embeddings
        """
        try:
            # Buscar uma amostra para calcular estatísticas
            embeddings = self.fetch_embeddings()

            if not embeddings:
                return {
                    "total_embeddings": 0,
                    "by_origin": {},
                    "latest_date": None,
                    "oldest_date": None
                }

            # Calcular estatísticas
            by_origin: Dict[str, int] = {}
            dates = []

            for embedding in embeddings:
                origin = embedding.get("origin", "unknown")
                by_origin[origin] = by_origin.get(origin, 0) + 1

                created_at = embedding.get("created_at")
                if created_at:
                    dates.append(created_at)

            stats = {
                "total_embeddings": len(embeddings),
                "by_origin": by_origin,
                "latest_date": max(dates) if dates else None,
                "oldest_date": min(dates) if dates else None,
                "sample_size": len(embeddings)
            }

            logger.info("Statistics calculated successfully")
            return stats

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {
                "total_embeddings": 0,
                "by_origin": {},
                "error": str(e)
            }

    def search_all_embeddings_like(
        self,
        keyword: str
    ) -> List[Dict]:
        """
        Busca embeddings que contenham a palavra-chave em qualquer campo.

        Parameters
        ----------
        keyword : str
            Palavra-chave para buscar
        max_results : int
            Máximo de resultados a retornar

        Returns
        -------
        List[Dict]
            Lista de embeddings encontrados
        """
        try:
            # Usar busca por texto que já filtra por conteúdo
            embeddings = self.query_embeddings_by_text(keyword)

            additional_embeddings = self.fetch_embeddings(
                search_query=keyword
            )

            # Combinar resultados evitando duplicatas
            existing_ids = {emb.get('id') for emb in embeddings}
            for emb in additional_embeddings:
                if emb.get(
                    'id'
                ) not in existing_ids and len(
                    embeddings
                ):
                    title = emb.get('title', '').lower()
                    content = emb.get('content', '').lower()
                    keyword_lower = keyword.lower()

                    score = 0.0
                    if keyword_lower in title:
                        score += 0.5
                    if keyword_lower in content:
                        score += 0.3

                    emb['similarity_score'] = score
                    embeddings.append(emb)

            logger.info(
                f"""Found {
                    len(embeddings)
                } embeddings matching keyword '{keyword}'"""
            )
            return embeddings

        except Exception as e:
            logger.error(f"Error searching embeddings by keyword: {e}")
            return []

    def health_check(self) -> bool:
        """
        Verifica se o serviço de embeddings está funcionando.

        Returns
        -------
        bool
            True se o serviço está disponível
        """
        try:
            # Tentar autenticar
            if not self.auth_token:
                if not self.authenticate():
                    return False

            # Testar busca simples
            embeddings_url = f"{self.api_base_url}/embeddings/"
            headers = self.get_headers()

            response = requests.get(
                embeddings_url,
                headers=headers,
                params={"limit": 1},
                timeout=5
            )

            healthy = response.status_code in [200, 401]
            logger.info(f"Health check: {'OK' if healthy else 'FAILED'}")
            return healthy

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
