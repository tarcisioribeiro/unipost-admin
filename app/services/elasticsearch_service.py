"""
Elasticsearch service for text search and retrieval.

This module provides functionality to search for relevant text content
from Elasticsearch to be used as context for text generation.
"""

from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch, exceptions
import streamlit as st
# from sentence_transformers import SentenceTransformer

from ..config.settings import settings


class ElasticsearchService:
    """
    Service class for interacting with Elasticsearch.

    This service handles text search, vector similarity search,
    and content retrieval from the Elasticsearch cluster.
    """

    def __init__(self) -> None:
        """Initialize the Elasticsearch service."""
        self.client = self._create_client()
        # self.model = SentenceTransformer(
        #     'sentence-transformers/all-MiniLM-L6-v2')
        self.index_name = "unipost_content"

    def _create_client(self) -> Optional[Elasticsearch]:
        """
        Create Elasticsearch client with authentication.

        Returns
        -------
        Optional[Elasticsearch]
            Configured Elasticsearch client or None if connection fails
        """
        try:
            if settings.elasticsearch_username and settings.elasticsearch_password:
                client = Elasticsearch(
                    settings.elasticsearch_url,
                    basic_auth=(
                        settings.elasticsearch_username,
                        settings.elasticsearch_password
                    ),
                    verify_certs=False,
                    ssl_show_warn=False
                )
            else:
                client = Elasticsearch(settings.elasticsearch_url)

            # Test connection
            if client.ping():
                return client
            else:
                st.error("Falha ao conectar com Elasticsearch")
                return None

        except Exception as e:
            st.error(f"Erro na configuração do Elasticsearch: {str(e)}")
            return None

    def search_content(
            self, query: str, size: int = 10) -> List[Dict[str, Any]]:
        """
        Search for content using text query.

        Parameters
        ----------
        query : str
            The search query text
        size : int, optional
            Maximum number of results to return (default: 10)

        Returns
        -------
        List[Dict[str, Any]]
            List of matching documents with metadata
        """
        if not self.client:
            return []

        try:
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content", "tags"],
                        "type": "best_fields"
                    }
                },
                "highlight": {
                    "fields": {
                        "content": {},
                        "title": {}
                    }
                },
                "size": size,
                "_source": ["title", "content", "timestamp", "tags", "source"]
            }

            response = self.client.search(
                index=self.index_name,
                body=search_body
            )

            results = []
            for hit in response["hits"]["hits"]:
                result = {
                    "score": hit["_score"],
                    "source": hit["_source"],
                    "highlight": hit.get("highlight", {})
                }
                results.append(result)

            return results

        except exceptions.ElasticsearchException as e:
            st.error(f"Erro na busca do Elasticsearch: {str(e)}")
            return []

    def vector_search(self, query: str, size: int = 5) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using sentence embeddings.

        Parameters
        ----------
        query : str
            The query text to encode and search for
        size : int, optional
            Maximum number of results to return (default: 5)

        Returns
        -------
        List[Dict[str, Any]]
            List of similar documents based on vector similarity
        """
        if not self.client:
            return []

        try:
            # Generate query vector
            query_vector = self.model.encode(query).tolist()

            search_body = {
                "query": {
                    "script_score": {
                        "query": {
                            "match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                            "params": {
                                "query_vector": query_vector}}}},
                "size": size,
                "_source": [
                    "title",
                    "content",
                    "timestamp",
                            "tags",
                    "source"]}

            response = self.client.search(
                index=self.index_name,
                body=search_body
            )

            results = []
            for hit in response["hits"]["hits"]:
                result = {
                    "score": hit["_score"],
                    "source": hit["_source"]
                }
                results.append(result)

            return results

        except exceptions.ElasticsearchException as e:
            st.error(f"Erro na busca vetorial: {str(e)}")
            return []

    def get_context_for_topic(self, topic: str) -> str:
        """
        Get relevant context for a given topic.

        Parameters
        ----------
        topic : str
            The topic to search context for

        Returns
        -------
        str
            Formatted context string from search results
        """
        # Combine text and vector search results
        text_results = self.search_content(topic, size=3)
        vector_results = self.vector_search(topic, size=2)

        all_results = text_results + vector_results

        if not all_results:
            return ""

        # Format context from results
        context_parts = []
        seen_content = set()

        for result in all_results:
            content = result["source"]["content"]
            title = result["source"].get("title", "")

            # Avoid duplicate content
            if content not in seen_content:
                seen_content.add(content)

                if title:
                    context_parts.append(f"**{title}**\n{content}")
                else:
                    context_parts.append(content)

        return "\n\n".join(context_parts)

    def check_connection(self) -> bool:
        """
        Check if Elasticsearch connection is active.

        Returns
        -------
        bool
            True if connected, False otherwise
        """
        if not self.client:
            return False

        try:
            return self.client.ping()
        except Exception:
            return False
