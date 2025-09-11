import redis
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RedisService:
    """
    Serviço para interação com Redis.
    Responsável pelo armazenamento em cache dos embeddings obtidos via API.
    """

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """
        Inicializa o cliente Redis.

        Parameters
        ----------
        host : str
            Host do Redis
        port : int
            Porta do Redis
        db : int
            Banco de dados Redis
        """
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True
            )
            self.client.ping()
            logger.info(f"Redis client initialized: {host}:{port}")
        except Exception as e:
            logger.error(f"Error initializing Redis client: {e}")
            self.client = redis.Redis()

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
