import redis
import json
import hashlib
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class RedisService:
    """
    Serviço para interação com Redis.
    Responsável pelo armazenamento em cache dos embeddings obtidos via API.
    """

    def __init__(self, host: str = None, port: int = 6379, db: int = 0):
        """
        Inicializa o cliente Redis.

        Parameters
        ----------
        host : str
            Host do Redis (se None, usa variável de ambiente)
        port : int
            Porta do Redis
        db : int
            Banco de dados Redis
        """
        try:
            # Usar REDIS_URL se disponível, senão usar parâmetros
            redis_url = os.getenv('REDIS_URL')
            if redis_url:
                self.client = redis.from_url(
                    redis_url,
                    decode_responses=True
                )
                logger.info(f"Redis client initialized from URL: {redis_url}")
            else:
                # Fallback para configuração manual
                if host is None:
                    host = 'localhost'
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True
                )
                logger.info(f"Redis client initialized: {host}:{port}")
            
            self.client.ping()
        except Exception as e:
            logger.error(f"Error initializing Redis client: {e}")
            # Fallback para cliente padrão (desconectado)
            self.client = redis.Redis(decode_responses=True)

    def cache_embeddings_by_word(self,
                                 word: str,
                                 embeddings_data: List[Dict],
                                 expiration: int = 86400):
        """
        Armazena embeddings de uma palavra específica no cache Redis.

        Parameters
        ----------
        word : str
            Palavra consultada
        embeddings_data : List[Dict]
            Lista de embeddings para a palavra
        expiration : int
            Tempo de expiração em segundos
        """
        try:
            if not self.client:
                return

            cache_key = f"word_embeddings:{hashlib.md5(word.encode()).hexdigest()}"
            
            cache_data = {
                "word": word,
                "embeddings": embeddings_data,
                "cached_at": datetime.now().isoformat(),
                "total_found": len(embeddings_data)
            }
            
            self.client.setex(
                cache_key,
                expiration,
                json.dumps(cache_data, ensure_ascii=False)
            )
            logger.info(f"Word embeddings cached: {word} ({len(embeddings_data)} results)")
        except Exception as e:
            logger.error(f"Error caching word embeddings: {e}")

    def get_cached_embeddings_by_word(self, word: str) -> Optional[List[Dict]]:
        """
        Recupera embeddings em cache para uma palavra específica.

        Parameters
        ----------
        word : str
            Palavra para buscar no cache

        Returns
        -------
        Optional[List[Dict]]
            Lista de embeddings ou None se não encontrado
        """
        try:
            if not self.client:
                return None

            cache_key = f"word_embeddings:{hashlib.md5(word.encode()).hexdigest()}"
            cached_data = self.client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                embeddings = data.get("embeddings", [])
                logger.info(f"Retrieved cached embeddings for word: {word} ({len(embeddings)} results)")
                return embeddings
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached word embeddings: {e}")
            return None

    def cache_embeddings(self,
                         query: str,
                         embeddings_data: Dict,
                         expiration: int = 86400):
        """
        Armazena embeddings obtidos via API no cache Redis.

        Parameters
        ----------
        query : str
            Query original
        embeddings_data : Dict
            Dados dos embeddings (textos similares, metadados, etc)
        expiration : int
            Tempo de expiração em segundos (padrão: 24 horas)
        """
        try:
            if not self.client:
                logger.error("Redis client not initialized")
                return

            cache_key = f"embeddings:{hashlib.md5(query.encode()).hexdigest()}"
            cache_data = {
                'query': query,
                'embeddings_data': embeddings_data,
                'timestamp': datetime.now().isoformat()
            }

            self.client.setex(
                cache_key,
                expiration,
                json.dumps(cache_data)
            )

            logger.info(f"Cached embeddings for query: {query}")

        except Exception as e:
            logger.error(f"Error caching embeddings: {e}")

    def get_cached_embeddings(self, query: str) -> Optional[Dict]:
        """
        Recupera embeddings do cache Redis.

        Parameters
        ----------
        query : str
            Query para busca no cache

        Returns
        -------
        Optional[Dict]
            Dados do cache ou None
        """
        try:
            if not self.client:
                return None

            cache_key = f"embeddings:{hashlib.md5(query.encode()).hexdigest()}"
            cached_data = self.client.get(cache_key)

            if cached_data:
                result = json.loads(str(cached_data))
                logger.info(f"Found cached embeddings for query: {query}")
                return result.get('embeddings_data')

            return None

        except Exception as e:
            logger.error(f"Error retrieving cached embeddings: {e}")
            return None

    def clear_cache(self):
        """
        Limpa todo o cache Redis.
        """
        try:
            if not self.client:
                logger.error("Redis client not initialized")
                return False

            self.client.flushdb()
            logger.info("Redis cache cleared")
            return True

        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            return False

    def get_all_keys(self, pattern: str = "*") -> list:
        """
        Obtém todas as chaves que correspondem ao padrão.

        Parameters
        ----------
        pattern : str
            Padrão para buscar chaves (default: "*")

        Returns
        -------
        list
            Lista de chaves encontradas
        """
        try:
            if not self.client:
                return []
            keys = self.client.keys(pattern)
            return [
                key.decode(
                    'utf-8'
                ) if isinstance(
                    key,
                    bytes
                ) else key for key in keys  # type: ignore
            ]
        except Exception as e:
            logger.error(f"Error getting Redis keys: {e}")
            return []

    def get_key_value(self, key: str):
        """
        Obtém o valor de uma chave.

        Parameters
        ----------
        key : str
            Nome da chave

        Returns
        -------
        Any
            Valor da chave ou None se não encontrada
        """
        try:
            if not self.client:
                return None

            key_type = self.client.type(key)
            if key_type == "string":
                value = self.client.get(key)
                try:
                    return json.loads(value) if value else None  # type: ignore
                except Exception:
                    return value
            elif key_type == "hash":
                return self.client.hgetall(key)
            elif key_type == "list":
                return self.client.lrange(key, 0, -1)
            elif key_type == "set":
                return list(self.client.smembers(key))  # type: ignore
            else:
                return self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting key value: {e}")
            return None

    def get_key_type(self, key: str) -> str:
        """
        Obtém o tipo de uma chave.

        Parameters
        ----------
        key : str
            Nome da chave

        Returns
        -------
        str
            Tipo da chave
        """
        try:
            if not self.client:
                return "unknown"
            key_type = self.client.type(key)
            return key_type.decode(
                'utf-8'
            ) if isinstance(key_type, bytes) else key_type   # type: ignore
        except Exception as e:
            logger.error(f"Error getting key type: {e}")
            return "unknown"

    def get_key_ttl(self, key: str) -> int:
        """
        Obtém o TTL (tempo de vida) de uma chave.

        Parameters
        ----------
        key : str
            Nome da chave

        Returns
        -------
        int
            TTL em segundos (-1 se não expira, -2 se não existe)
        """
        try:
            if not self.client:
                return -2
            return self.client.ttl(key)  # type: ignore
        except Exception as e:
            logger.error(f"Error getting key TTL: {e}")
            return -2

    def is_connected(self) -> bool:
        """
        Verifica se a conexão com Redis está ativa.

        Returns
        -------
        bool
            True se conectado, False caso contrário
        """
        try:
            if not self.client:
                return False
            result = self.client.ping()
            return bool(result)
        except Exception as e:
            logger.error(f"Error checking Redis connection: {e}")
            return False
