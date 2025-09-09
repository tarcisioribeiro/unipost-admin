"""
Elasticsearch service for text search and retrieval.

This module provides functionality to search for relevant text content
from Elasticsearch to be used as context for text generation.
"""

from typing import List, Dict, Any, Optional
import streamlit as st
import requests
import json
from sentence_transformers import SentenceTransformer

from config.settings import settings


class ElasticsearchService:
    """
    Service class for interacting with Elasticsearch.

    This service handles text search, vector similarity search,
    and content retrieval from the Elasticsearch cluster.
    """

    def __init__(self) -> None:
        """Initialize the Elasticsearch service."""
        self.es_url = settings.es_host
        self.username = settings.es_user
        self.password = settings.es_pass
        self.index_name = "unipost_content"
        self.session = requests.Session()
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Configure session with authentication
        if self.username and self.password:
            self.session.auth = (self.username, self.password)

    def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Optional[requests.Response]:
        """Make authenticated request to Elasticsearch."""
        try:
            url = f"{self.es_url}/{endpoint.lstrip('/')}"
            response = self.session.request(
                method, url, timeout=30, **kwargs
            )
            return response
        except Exception as e:
            st.error(f"Erro na requisição ao Elasticsearch: {str(e)}")
            return None

    def search_content(
        self, query: str, size: int = 10
    ) -> List[Dict[str, Any]]:
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
                "_source": [
                    "title", "content", "timestamp",
                    "tags", "source", "category"
                ]
            }

            response = self._make_request(
                "POST",
                f"{self.index_name}/_search",
                headers={"Content-Type": "application/json"},
                data=json.dumps(search_body)
            )

            if not response or response.status_code != 200:
                error_msg = (
                    response.status_code if response else 'No response'
                )
                st.error(f"Erro na busca: {error_msg}")
                return []

            data = response.json()
            results = []

            for hit in data.get("hits", {}).get("hits", []):
                result = {
                    "score": hit.get("_score", 0),
                    "source": hit.get("_source", {}),
                    "highlight": hit.get("highlight", {})
                }
                results.append(result)

            return results

        except Exception as e:
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
        try:
            # Generate query embedding
            query_embedding = self.sentence_model.encode(query).tolist()

            # Elasticsearch vector search query
            search_body = {
                "size": size,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": ("cosineSimilarity(params.query_vector, "
                                       "'content_vector') + 1.0"),
                            "params": {"query_vector": query_embedding}
                        }
                    }
                },
                "_source": ["title", "content", "url", "timestamp"],
                "highlight": {
                    "fields": {
                        "content": {
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        }
                    }
                }
            }

            # Execute the search
            url = f"{self.es_url}/{self.index_name}/_search"
            response = self.session.post(
                url,
                headers={"Content-Type": "application/json"},
                json=search_body,
                timeout=30
            )
            response.raise_for_status()

            # Parse results
            search_result = response.json()
            results = []

            for hit in search_result.get("hits", {}).get("hits", []):
                result = {
                    "score": hit.get("_score", 0),
                    "source": hit.get("_source", {}),
                    "highlight": hit.get("highlight", {})
                }
                results.append(result)

            return results

        except Exception as e:
            st.error(f"Erro na busca vetorial do Elasticsearch: {str(e)}")
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
        # Use only text search results for now
        text_results = self.search_content(topic, size=5)

        all_results = text_results

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
        try:
            response = self._make_request("GET", "_cluster/health")
            return response is not None and response.status_code == 200
        except Exception:
            return False
