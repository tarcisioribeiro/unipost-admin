"""
Text generation service for creating natural language content.

This module provides text generation capabilities using AI models,
integrating with search results to create contextually relevant content.
"""

from typing import Dict, Any, Optional, List
import requests
import streamlit as st
from datetime import datetime

from config.settings import settings
from .elasticsearch_service import ElasticsearchService
from .redis_service import RedisService


class TextGenerationService:
    """
    Service class for text generation using AI models.

    This service handles text generation requests, context preparation,
    and integration with search and caching services.
    """

    def __init__(self) -> None:
        """Initialize the text generation service."""
        self.elasticsearch_service = ElasticsearchService()
        self.redis_service = RedisService()
        self.base_url = settings.django_api_url

    def generate_text(
        self,
        topic: str,
        model: Optional[str] = None,
        user_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate text content based on topic and context.

        Parameters
        ----------
        topic : str
            The topic/theme for text generation
        model : str, optional
            The model to use for generation (default from settings)
        user_token : str, optional
            User authentication token

        Returns
        -------
        Optional[Dict[str, Any]]
            Generated text data with metadata or None if failed
        """
        try:
            # Check for cached results first
            cached_result = self.redis_service.get_cached_search_results(topic)

            if cached_result:
                context = self._format_context_from_cache(cached_result)
            else:
                # Get context from Elasticsearch
                context = self.elasticsearch_service.get_context_for_topic(
                    topic)

                if not context:
                    st.warning(
                        "Nenhum contexto encontrado para o tema especificado.")
                    return None

                # Cache the search results
                search_results = self.elasticsearch_service.search_content(
                    topic)
                self.redis_service.cache_search_results(topic, search_results)

            # Prepare the generation request
            generation_data = self._prepare_generation_request(
                topic, context, model or settings.default_model
            )

            # Send request to Django API
            headers = {}
            if user_token:
                headers["Authorization"] = f"Bearer {user_token}"

            response = requests.post(
                f"{self.base_url}/api/generate/",
                json=generation_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                # Add metadata
                result.update({
                    "topic": topic,
                    "context_length": len(context),
                    "generated_at": datetime.now().isoformat(),
                    "model_used": model or settings.default_model
                })

                return result
            else:
                st.error(f"Erro na geração de texto: {response.status_code}")
                return None

        except requests.RequestException as e:
            st.error(f"Erro de conexão na geração: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Erro inesperado na geração: {str(e)}")
            return None

    def _prepare_generation_request(
        self,
        topic: str,
        context: str,
        model: str
    ) -> Dict[str, Any]:
        """
        Prepare the text generation request payload.

        Parameters
        ----------
        topic : str
            The topic for generation
        context : str
            The context from search results
        model : str
            The model to use

        Returns
        -------
        Dict[str, Any]
            Request payload for text generation
        """
        prompt = self._build_prompt(topic, context)

        return {
            "model": model,
            "prompt": prompt,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "topic": topic,
            "context_provided": bool(context)
        }

    def _build_prompt(self, topic: str, context: str) -> str:
        """
        Build the complete prompt for text generation.

        Parameters
        ----------
        topic : str
            The topic for generation
        context : str
            The context information

        Returns
        -------
        str
            Complete formatted prompt
        """
        prompt_template = """
Com base no contexto fornecido abaixo, crie um texto natural e envolvente sobre o tema: "{topic}"

CONTEXTO:
{context}

INSTRUÇÕES:
- Crie um texto informativo e bem estruturado
- Use linguagem clara e objetiva em português brasileiro
- Mantenha um tom profissional mas acessível
- Incorpore informações do contexto de forma natural
- O texto deve ter entre 300 a 500 palavras
- Use parágrafos bem organizados

TEXTO:
"""

        return prompt_template.format(
            topic=topic,
            context=context if context else "Nenhum contexto específico fornecido.")

    def _format_context_from_cache(
            self, cached_results: List[Dict[str, Any]]) -> str:
        """
        Format context from cached search results.

        Parameters
        ----------
        cached_results : List[Dict[str, Any]]
            Cached search results

        Returns
        -------
        str
            Formatted context string
        """
        context_parts = []

        for result in cached_results:
            source = result.get("source", {})
            content = source.get("content", "")
            title = source.get("title", "")

            if content:
                if title:
                    context_parts.append(f"**{title}**\n{content}")
                else:
                    context_parts.append(content)

        return "\n\n".join(context_parts)

    def approve_text(self, text_id: str, user_token: Optional[str]) -> bool:
        """
        Approve a generated text via webhook.

        Parameters
        ----------
        text_id : str
            The ID of the text to approve
        user_token : str
            User authentication token

        Returns
        -------
        bool
            True if approval successful, False otherwise
        """
        return self._update_text_status(text_id, True, user_token)

    def reject_text(self, text_id: str, user_token: Optional[str]) -> bool:
        """
        Reject a generated text via webhook.

        Parameters
        ----------
        text_id : str
            The ID of the text to reject
        user_token : str
            User authentication token

        Returns
        -------
        bool
            True if rejection successful, False otherwise
        """
        return self._update_text_status(text_id, False, user_token)

    def _update_text_status(
        self,
        text_id: str,
        is_approved: bool,
        user_token: str
    ) -> bool:
        """
        Update text approval status via Django API.

        Parameters
        ----------
        text_id : str
            The ID of the text to update
        is_approved : bool
            Approval status
        user_token : str
            User authentication token

        Returns
        -------
        bool
            True if update successful, False otherwise
        """
        try:
            headers = {"Authorization": f"Bearer {user_token}"}
            data = {"is_approved": is_approved}

            response = requests.patch(
                f"{self.base_url}/api/texts/{text_id}/",
                json=data,
                headers=headers,
                timeout=10
            )

            return response.status_code in [200, 204]

        except requests.RequestException as e:
            st.error(f"Erro ao atualizar status: {str(e)}")
            return False

    def get_available_models(self) -> List[str]:
        """
        Get list of available models for text generation.

        Returns
        -------
        List[str]
            List of available model names
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/models/",
                timeout=5
            )

            if response.status_code == 200:
                return response.json().get("models", [settings.default_model])

        except requests.RequestException:
            pass

        # Return default model if API call fails
        return [settings.default_model]
