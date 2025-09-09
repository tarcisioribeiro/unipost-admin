import redis
import json
import hashlib
from datetime import datetime
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class RedisService:
    """
    Serviço para interação com Redis.
    Responsável pelo armazenamento em cache dos vetores consultados.
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

    def cache_vectors(self,
                      query: str,
                      vectors: List[List[float]],
                      texts: List[str],
                      expiration: int = 86400):
        """
        Armazena vetores no cache Redis.

        Parameters
        ----------
        query : str
            Query original
        vectors : List[List[float]]
            Lista de vetores
        texts : List[str]
            Textos correspondentes
        expiration : int
            Tempo de expiração em segundos (padrão: 24 horas)
        """
        try:
            if not self.client:
                logger.error("Redis client not initialized")
                return

            cache_key = f"vectors:{hashlib.md5(query.encode()).hexdigest()}"
            cache_data = {
                'query': query,
                'vectors': vectors,
                'texts': texts,
                'timestamp': datetime.now().isoformat()
            }

            self.client.setex(
                cache_key,
                expiration,
                json.dumps(cache_data)
            )

            logger.info(f"Cached vectors for query: {query}")

        except Exception as e:
            logger.error(f"Error caching vectors: {e}")

    def get_cached_vectors(self, query: str) -> Optional[Dict]:
        """
        Recupera vetores do cache Redis.

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

            cache_key = f"vectors:{hashlib.md5(query.encode()).hexdigest()}"
            cached_data = self.client.get(cache_key)

            if cached_data:
                logger.info(f"Found cached vectors for query: {query}")
                return json.loads(cached_data)  # type: ignore

            return None

        except Exception as e:
            logger.error(f"Error retrieving cached vectors: {e}")
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
