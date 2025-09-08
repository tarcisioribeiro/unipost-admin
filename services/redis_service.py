"""
Redis service for caching search results and temporary data.

This module provides caching functionality using Redis to store
search results and improve application performance.
"""

from typing import Optional, Dict, Any, List
import json
import redis
import pandas as pd
import streamlit as st

from config.settings import settings


class RedisService:
    """
    Service class for Redis caching operations.

    This service handles caching of search results, user sessions,
    and temporary data storage to improve application performance.
    """

    def __init__(self) -> None:
        """Initialize the Redis service."""
        self.client = self._create_client()
        self.default_ttl = 3600  # 1 hour default TTL

    def _create_client(self) -> Optional[redis.Redis]:
        """
        Create Redis client connection.

        Returns
        -------
        Optional[redis.Redis]
            Redis client instance or None if connection fails
        """
        try:
            client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )

            # Test connection
            client.ping()
            return client

        except redis.RedisError as e:
            st.error(f"Erro ao conectar com Redis: {str(e)}")
            return None

    def set_cache(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set a value in cache with optional TTL.

        Parameters
        ----------
        key : str
            The cache key
        value : Any
            The value to cache (will be JSON serialized)
        ttl : Optional[int]
            Time to live in seconds (default: 1 hour)

        Returns
        -------
        bool
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
            ttl = ttl or self.default_ttl

            return self.client.setex(
                key,
                ttl,
                serialized_value
            )

        except (redis.RedisError, json.JSONEncodeError) as e:
            st.error(f"Erro ao salvar no cache: {str(e)}")
            return False

    def get_cache(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Parameters
        ----------
        key : str
            The cache key to retrieve

        Returns
        -------
        Optional[Any]
            The cached value or None if not found/expired
        """
        if not self.client:
            return None

        try:
            cached_value = self.client.get(key)

            if cached_value is None:
                return None

            return json.loads(cached_value)

        except (redis.RedisError, json.JSONDecodeError) as e:
            st.error(f"Erro ao recuperar do cache: {str(e)}")
            return None

    def delete_cache(self, key: str) -> bool:
        """
        Delete a key from cache.

        Parameters
        ----------
        key : str
            The cache key to delete

        Returns
        -------
        bool
            True if deleted, False otherwise
        """
        if not self.client:
            return False

        try:
            return bool(self.client.delete(key))

        except redis.RedisError as e:
            st.error(f"Erro ao deletar do cache: {str(e)}")
            return False

    def cache_search_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> bool:
        """
        Cache search results for a specific query.

        Parameters
        ----------
        query : str
            The search query used as cache key
        results : List[Dict[str, Any]]
            The search results to cache

        Returns
        -------
        bool
            True if cached successfully, False otherwise
        """
        cache_key = f"search:{hash(query)}"
        cache_data = {
            "query": query,
            "results": results,
            "timestamp": str(pd.Timestamp.now())
        }

        return self.set_cache(cache_key, cache_data, ttl=1800)

    def get_cached_search_results(self, query: str) -> Optional[
            List[Dict[str, Any]]]:
        """
        Get cached search results for a query.

        Parameters
        ----------
        query : str
            The search query to look up

        Returns
        -------
        Optional[List[Dict[str, Any]]]
            Cached search results or None if not found
        """
        cache_key = f"search:{hash(query)}"
        cached_data = self.get_cache(cache_key)

        if cached_data and cached_data.get("query") == query:
            return cached_data.get("results")

        return None

    def cache_user_session(self, user_id: str,
                           session_data: Dict[str, Any]) -> bool:
        """
        Cache user session data.

        Parameters
        ----------
        user_id : str
            The user identifier
        session_data : Dict[str, Any]
            Session data to cache

        Returns
        -------
        bool
            True if cached successfully, False otherwise
        """
        cache_key = f"session:{user_id}"
        return self.set_cache(cache_key, session_data, ttl=7200)

    def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached user session data.

        Parameters
        ----------
        user_id : str
            The user identifier

        Returns
        -------
        Optional[Dict[str, Any]]
            Cached session data or None if not found
        """
        cache_key = f"session:{user_id}"
        return self.get_cache(cache_key)

    def clear_user_session(self, user_id: str) -> bool:
        """
        Clear cached user session data.

        Parameters
        ----------
        user_id : str
            The user identifier

        Returns
        -------
        bool
            True if cleared successfully, False otherwise
        """
        cache_key = f"session:{user_id}"
        return self.delete_cache(cache_key)

    def check_connection(self) -> bool:
        """
        Check if Redis connection is active.

        Returns
        -------
        bool
            True if connected, False otherwise
        """
        if not self.client:
            return False

        try:
            self.client.ping()
            return True
        except redis.RedisError:
            return False
