"""
Text generation service for creating natural language content.

This module provides text generation capabilities using AI models,
integrating with search results to create contextually relevant content.
"""

from typing import Dict, Any, Optional, List
import requests
import streamlit as st
from datetime import datetime
import openai

from config.settings import settings
from .elasticsearch_service import ElasticsearchService
from .redis_service import RedisService


class TextGenerationService:
    """
    Service class for text generation using AI models.

    This service handles text generation requests, context preparation,
    and integration with search and caching services for different
    social platforms.
    """

    # Social platform definitions from the API
    PLATFORMS = {
        'FCB': 'Facebook',
        'INT': 'Instagram',
        'TTK': 'Tiktok',
        'LKN': 'Linkedin'
    }

    def __init__(self) -> None:
        """Initialize the text generation service."""
        self.elasticsearch_service = ElasticsearchService()
        self.redis_service = RedisService()
        self.base_url = settings.django_api_url
        # Initialize OpenAI client if API key is provided
        self.openai_client = None
        if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
            try:
                self.openai_client = openai.OpenAI(
                    api_key=settings.openai_api_key
                )
            except Exception as e:
                st.warning(f"Falha ao inicializar cliente OpenAI: {e}")

    def generate_text(
        self,
        topic: str,
        platform: str = 'FCB',
        model: Optional[str] = None,
        user_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate text content based on topic, platform and context.

        Parameters
        ----------
        topic : str
            The topic/theme for text generation
        platform : str
            The social platform code (FCB, INT, TTK, LKN)
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
                    topic
                )

                if not context:
                    warning_msg = ("Nenhum contexto encontrado para "
                                   "o tema especificado.")
                    st.warning(warning_msg)
                    return None

                # Cache the search results
                search_results = self.elasticsearch_service.search_content(
                    topic
                )
                self.redis_service.cache_search_results(topic, search_results)

            # Prepare the generation request with platform-specific context
            generation_data = self._prepare_generation_request(
                topic, context, platform, model or settings.default_model
            )

            # Send request to Django API
            headers = {}
            if user_token:
                headers["Authorization"] = f"Bearer {user_token}"

            # Always use OpenAI for text generation when available
            if self.openai_client is not None:
                result = self._generate_with_openai(
                    topic, platform, context, generation_data
                )
                # Store result in Django API (REQUIRED)
                if result:
                    stored_result = self._store_in_django_api(result, headers)
                    if stored_result:
                        # Add the text ID from Django API to the result
                        result['text_id'] = int(
                            stored_result.get('id', 0)
                        )
                        result['stored'] = True
                        return result
                    else:
                        error_msg = ("Erro: Não foi possível armazenar "
                                     "o texto na API. Tente novamente.")
                        st.error(error_msg)
                        return None
                else:
                    return None
            else:
                error_msg = ("Cliente OpenAI não configurado. "
                             "Configure OPENAI_API_KEY no arquivo .env")
                st.error(error_msg)
                return None

        except requests.RequestException as e:
            error_msg = self._format_request_error(e)
            st.error(f"Erro de conexão na geração: {error_msg}")
            return None
        except Exception as e:
            if "openai" in str(type(e)).lower():
                st.error(f"Erro OpenAI: {self._format_openai_error(e)}")
            else:
                st.error(f"Erro inesperado na geração: {str(e)}")
            return None

    def _prepare_generation_request(
        self,
        topic: str,
        context: str,
        platform: str,
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
        platform : str
            The social platform code
        model : str
            The model to use

        Returns
        -------
        Dict[str, Any]
            Request payload for text generation
        """
        prompt = self._build_platform_specific_prompt(topic, context, platform)

        return {
            "model": model,
            "prompt": prompt,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "topic": topic,
            "platform": platform,
            "platform_name": self.PLATFORMS.get(platform, platform),
            "context_provided": bool(context)
        }

    def _build_platform_specific_prompt(
        self, topic: str, context: str, platform: str
    ) -> str:
        """
        Build platform-specific prompt for text generation.

        Parameters
        ----------
        topic : str
            The topic for generation
        context : str
            The context information
        platform : str
            The social platform code

        Returns
        -------
        str
            Complete formatted prompt optimized for the platform
        """
        platform_configs = self._get_platform_configs()
        config = platform_configs.get(platform, platform_configs['FCB'])

        platform_name = self.PLATFORMS.get(platform, platform)
        platform_upper = platform_name.upper()

        prompt_template = f"""
Com base no contexto fornecido abaixo, crie um texto otimizado para \
{platform_name} sobre o tema: "{topic}"

CONTEXTO:
{{context}}

INSTRUÇÕES ESPECÍFICAS PARA {platform_upper}:
{config['instructions']}

CARACTERÍSTICAS DO CONTEÚDO:
- Tamanho: {config['length']}
- Tom: {config['tone']}
- Formato: {config['format']}
- Hashtags: {config['hashtags']}
- Call to Action: {config['cta']}

TEXTO:
"""

        return prompt_template.format(
            context=(
                context if context else
                "Nenhum contexto específico fornecido."
            )
        )

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

    def approve_text(
        self,
        text_id: int,
        user_token: Optional[str] = None
    ) -> bool:
        """
        Approve a generated text by setting is_approved=True.

        Parameters
        ----------
        text_id : int
            The ID of the text to approve
        user_token : str, optional
            User authentication token

        Returns
        -------
        bool
            True if approval successful, False otherwise
        """
        return self._update_text_status(text_id, True, user_token)

    def reject_text(
        self, text_id: int, user_token: Optional[str] = None
    ) -> bool:
        """
        Reject/discard a generated text by keeping is_approved=False.

        Parameters
        ----------
        text_id : int
            The ID of the text to reject
        user_token : str, optional
            User authentication token

        Returns
        -------
        bool
            True if rejection successful, False otherwise
        """
        return self._update_text_status(text_id, False, user_token)

    def _update_text_status(
        self,
        text_id: int,
        is_approved: bool,
        user_token: Optional[str] = None
    ) -> bool:
        """
        Update text approval status via Django API.

        Parameters
        ----------
        text_id : int
            The ID of the text to update
        is_approved : bool
            Approval status
        user_token : str, optional
            User authentication token

        Returns
        -------
        bool
            True if update successful, False otherwise
        """
        try:
            headers = {"Content-Type": "application/json"}
            if user_token:
                headers["Authorization"] = f"Bearer {user_token}"

            data = {"is_approved": is_approved}

            response = requests.patch(
                f"{self.base_url}/api/v1/texts/{text_id}/",
                json=data,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 204]:
                return True
            else:
                error_detail = self._extract_api_error_detail(response)
                st.error(
                    f"Erro ao atualizar status (Status "
                    f"{response.status_code}): {error_detail}"
                )
                return False

        except requests.RequestException as e:
            error_msg = self._format_request_error(e)
            st.error(f"Erro de conexão ao atualizar status: {error_msg}")
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
                f"{self.base_url}/api/v1/models/",
                timeout=5
            )

            if response.status_code == 200:
                return response.json().get("models", [settings.default_model])

        except requests.RequestException:
            pass

        # Return available models including GPT-4o-mini
        available_models = [settings.default_model]
        if settings.default_model != 'gpt-4o-mini':
            available_models.append('gpt-4o-mini')
        return available_models

    def _get_platform_configs(self) -> Dict[str, Dict[str, str]]:
        """
        Get platform-specific configuration for text generation.

        Returns
        -------
        Dict[str, Dict[str, str]]
            Platform-specific configurations
        """
        return {
            'FCB': {
                'instructions': '''- Use linguagem conversacional e acessível
- Incentive interação (curtidas, comentários, compartilhamentos)
- Inclua perguntas para engajamento
- Use emojis moderadamente''',
                'length': '150-300 palavras',
                'tone': 'Amigável e conversacional',
                'format': 'Parágrafos curtos com quebras de linha',
                'hashtags': '3-5 hashtags relevantes',
                'cta': 'Perguntas ou convites para comentar'
            },
            'INT': {
                'instructions': '''- Foque no visual e storytelling
- Use linguagem jovem e autêntica
- Seja conciso e impactante
- Inclua elementos visuais na narrativa''',
                'length': '100-200 palavras',
                'tone': 'Casual, inspirador e visual',
                'format': 'Texto curto com quebras estratégicas',
                'hashtags': '10-15 hashtags mixando populares e de nicho',
                'cta': 'Stories, saves ou interações visuais'
            },
            'TTK': {
                'instructions': '''- Seja criativo e viral
- Use trends e linguagem da internet
- Crie ganchos nos primeiros 3 segundos
- Inclua elementos de surpresa ou humor''',
                'length': '50-150 palavras',
                'tone': 'Energético, divertido e trend-aware',
                'format': 'Frases curtas e impactantes',
                'hashtags': '5-8 hashtags trending e específicos',
                'cta': 'Engajamento através de trends e challenges'
            },
            'LKN': {
                'instructions': '''- Mantenha tom profissional e informativo
- Inclua insights e valor agregado
- Use dados e estatísticas quando possível
- Foque em networking e crescimento profissional''',
                'length': '200-400 palavras',
                'tone': 'Profissional, autorativo e educativo',
                'format': 'Parágrafos bem estruturados com bullet points',
                'hashtags': '3-7 hashtags profissionais e de indústria',
                'cta': 'Convites para conexão ou discussão profissional'
            }
        }

    def _generate_with_openai(
        self,
        topic: str,
        platform: str,
        context: str,
        generation_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate text using OpenAI directly.

        Parameters
        ----------
        topic : str
            The topic for generation
        platform : str
            The social platform code
        context : str
            The context from search
        generation_data : Dict[str, Any]
            Generation request data

        Returns
        -------
        Optional[Dict[str, Any]]
            Generated text data or None if failed
        """
        try:
            if not self.openai_client:
                st.error("Cliente OpenAI não inicializado")
                return None

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um especialista em criação de conteúdo "
                            "para redes sociais. Crie textos otimizados para "
                            "cada plataforma seguindo as melhores práticas "
                            "de engajamento."
                        )
                    },
                    {"role": "user", "content": generation_data["prompt"]}
                ],
                max_tokens=generation_data["max_tokens"],
                temperature=generation_data["temperature"]
            )

            content = response.choices[0].message.content

            return {
                "content": content,
                "topic": topic,
                "platform": platform,
                "platform_name": self.PLATFORMS.get(platform, platform),
                "context_length": len(context),
                "generated_at": datetime.now().isoformat(),
                "model_used": "gpt-4o-mini",
                "tokens_used": (
                    response.usage.total_tokens if response.usage else 0
                ),
                "source": "openai_direct"
            }

        except Exception as e:
            st.error(f"Erro na geração OpenAI: {self._format_openai_error(e)}")
            return None

    def _store_in_django_api(
        self, result: Dict[str, Any], headers: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Store generated text in Django API (REQUIRED).

        Parameters
        ----------
        result : Dict[str, Any]
            Generated text result
        headers : Dict[str, str]
            Request headers with auth

        Returns
        -------
        Optional[Dict[str, Any]]
            API response with text ID if stored successfully, None if failed
        """
        try:
            # Prepare data for Django API storage according to Text model
            storage_data = {
                "theme": result.get("topic"),  # Maps to 'theme' field
                "platform": result.get("platform"),
                "content": result.get("content"),
                "is_approved": False  # Always start as False
            }

            response = requests.post(
                f"{self.base_url}/api/v1/texts/",
                json=storage_data,
                headers={**headers, "Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code in [200, 201]:
                return response.json()
            else:
                error_detail = self._extract_api_error_detail(response)
                st.error(
                    f"Erro ao armazenar na API Django (Status "
                    f"{response.status_code}): {error_detail}"
                )
                return None

        except requests.RequestException as e:
            error_msg = self._format_request_error(e)
            st.error(
                f"Erro de conexão ao armazenar na API Django: "
                f"{error_msg}"
            )
            return None
        except Exception as e:
            st.error(
                f"Erro inesperado ao armazenar na API Django: {str(e)}"
            )
            return None

    def _generate_with_django_api(
        self,
        generation_data: Dict[str, Any],
        headers: Dict[str, str],
        topic: str,
        platform: str,
        context: str,
        model: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate text using Django API.

        Parameters
        ----------
        generation_data : Dict[str, Any]
            Generation request data
        headers : Dict[str, str]
            Request headers
        topic : str
            The topic for generation
        platform : str
            The social platform code
        context : str
            The context from search
        model : Optional[str]
            The model to use

        Returns
        -------
        Optional[Dict[str, Any]]
            Generated text data or None if failed
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/generate/",
                json=generation_data,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                # Add metadata
                result.update({
                    "topic": topic,
                    "platform": platform,
                    "platform_name": self.PLATFORMS.get(platform, platform),
                    "context_length": len(context),
                    "generated_at": datetime.now().isoformat(),
                    "model_used": model or settings.default_model,
                    "source": "django_api"
                })

                return result
            else:
                error_detail = self._extract_api_error_detail(response)
                st.error(
                    f"Erro na geração de texto (Status "
                    f"{response.status_code}): {error_detail}"
                )
                return None

        except requests.Timeout:
            st.error("Timeout na geração de texto. Tente novamente.")
            return None
        except requests.ConnectionError:
            st.error(
                "Erro de conexão com a API. Verifique a conectividade."
            )
            return None

    def _extract_api_error_detail(
        self, response: requests.Response
    ) -> str:
        """
        Extract detailed error information from API response.

        Parameters
        ----------
        response : requests.Response
            The failed API response

        Returns
        -------
        str
            Formatted error message
        """
        try:
            error_data = response.json()
            if 'error' in error_data:
                return error_data['error']
            elif 'detail' in error_data:
                return error_data['detail']
            elif 'message' in error_data:
                return error_data['message']
            else:
                return (
                    f"Erro não especificado. Resposta: "
                    f"{response.text[:200]}"
                )
        except Exception:
            return (
                f"Erro ao processar resposta da API. Status: "
                f"{response.status_code}"
            )

    def _format_request_error(
        self, error: requests.RequestException
    ) -> str:
        """
        Format request errors with detailed information.

        Parameters
        ----------
        error : requests.RequestException
            The request exception

        Returns
        -------
        str
            Formatted error message
        """
        if isinstance(error, requests.Timeout):
            return "Timeout - A requisição demorou muito para responder"
        elif isinstance(error, requests.ConnectionError):
            return (
                "Erro de conexão - Verifique sua internet e a "
                "disponibilidade da API"
            )
        elif isinstance(error, requests.HTTPError):
            status = (
                error.response.status_code if error.response
                else 'desconhecido'
            )
            return f"Erro HTTP {status}"
        else:
            return str(error)

    def _format_openai_error(self, error) -> str:
        """
        Format OpenAI API errors with detailed information.

        Parameters
        ----------
        error : openai.error.OpenAIError
            The OpenAI exception

        Returns
        -------
        str
            Formatted error message
        """
        error_type = type(error).__name__
        if hasattr(error, 'user_message'):
            return f"{error_type}: {error.user_message}"
        elif hasattr(error, 'error') and hasattr(error.error, 'message'):
            return f"{error_type}: {error.error.message}"
        else:
            return f"{error_type}: {str(error)}"
