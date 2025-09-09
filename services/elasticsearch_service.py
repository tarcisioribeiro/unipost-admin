from elasticsearch import Elasticsearch
from typing import List, Dict
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """
    Serviço para interação com ElasticSearch.
    Responsável pela busca automática de textos.
    """

    def __init__(self):
        """
        Inicializa o cliente ElasticSearch usando configurações do .env.
        """
        try:
            es_host = os.getenv('ES_HOST')
            es_user = os.getenv('ES_USER')
            es_pass = os.getenv('ES_PASS')

            if es_host and es_user:
                # Configuração para ElasticSearch Cloud/remoto com autenticação
                self.client = Elasticsearch(
                    [es_host],
                    basic_auth=(es_user, es_pass) if es_pass else None,
                    verify_certs=True if 'https' in es_host else False,
                    ssl_show_warn=False
                )
                logger.info(f"ElasticSearch client initialized: {es_host}")
            else:
                # Fallback para configuração local
                self.client = Elasticsearch(
                    [{'host': 'localhost', 'port': 9200, 'scheme': 'http'}]
                )
                logger.info("ElasticSearch client initialized: localhost:9200")

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
