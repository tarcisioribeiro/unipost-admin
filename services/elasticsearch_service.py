from elasticsearch import Elasticsearch
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """
    Serviço para interação com ElasticSearch.
    Responsável pela busca automática de textos.
    """

    def __init__(self, host: str = 'localhost', port: int = 9200):
        """
        Inicializa o cliente ElasticSearch.

        Parameters
        ----------
        host : str
            Host do ElasticSearch
        port : int
            Porta do ElasticSearch
        """
        try:
            self.client = Elasticsearch(
                [{'host': host, 'port': port, 'scheme': 'http'}]
            )
            logger.info(f"ElasticSearch client initialized: {host}:{port}")
        except Exception as e:
            logger.error(f"Error initializing ElasticSearch client: {e}")
            self.client = None

    def search_texts(self, query: str, size: int = 10,
                     index: str = "texts") -> List[Dict]:
        """
        Realiza busca automática de textos no ElasticSearch.

        Parameters
        ----------
        query : str
            Consulta de busca
        size : int
            Número máximo de resultados
        index : str
            Nome do índice

        Returns
        -------
        List[Dict]
            Lista de textos encontrados
        """
        try:
            if not self.client:
                logger.error("ElasticSearch client not initialized")
                return []

            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "content", "tags", "author"]
                    }
                },
                "size": size,
                "_source": ["title", "content", "tags", "author", "created_at"]
            }

            response = self.client.search(
                index=index,
                body=search_body
            )

            texts = []
            for hit in response['hits']['hits']:
                text_data = {
                    'id': hit['_id'],
                    'title': hit['_source'].get('title', ''),
                    'content': hit['_source'].get('content', ''),
                    'tags': hit['_source'].get('tags', []),
                    'author': hit['_source'].get('author', ''),
                    'created_at': hit['_source'].get('created_at', ''),
                    'score': hit['_score']
                }
                texts.append(text_data)

            logger.info(f"Found {len(texts)} texts for query: {query}")
            return texts

        except Exception as e:
            logger.error(f"Error searching ElasticSearch: {e}")
            return []

    def is_connected(self) -> bool:
        """
        Verifica se a conexão com ElasticSearch está ativa.

        Returns
        -------
        bool
            True se conectado, False caso contrário
        """
        try:
            if not self.client:
                return False
            return self.client.ping()
        except Exception as e:
            logger.error(f"Error checking ElasticSearch connection: {e}")
            return False
