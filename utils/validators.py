"""
Validation utilities for UniPOST application.

This module contains validation functions for user inputs,
data integrity, and business logic validation.
"""

import re
from typing import Optional, List, Dict, Any, Tuple


def validate_topic(topic: str) -> Tuple[bool, Optional[str]]:
    """
    Validate topic input for text generation.

    Parameters
    ----------
    topic : str
        The topic text to validate

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_message)
    """
    if not topic or not topic.strip():
        return False, "Tema é obrigatório"

    topic = topic.strip()

    # Minimum length check
    if len(topic) < 5:
        return False, "Tema deve ter pelo menos 5 caracteres"

    # Maximum length check
    if len(topic) > 500:
        return False, "Tema deve ter no máximo 500 caracteres"

    # Check for potentially harmful content
    harmful_patterns = [
        r"<script.*?>",
        r"javascript:",
        r"vbscript:",
        r"onload=",
        r"onerror="
    ]

    for pattern in harmful_patterns:
        if re.search(pattern, topic, re.IGNORECASE):
            return False, "Tema contém conteúdo não permitido"

    return True, None


def validate_model_selection(model: str,
                             available_models: List[str]) -> Tuple[
        bool, Optional[str]]:
    """
    Validate model selection.

    Parameters
    ----------
    model : str
        Selected model name
    available_models : List[str]
        List of available models

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_message)
    """
    if not model:
        return False, "Modelo é obrigatório"

    if model not in available_models:
        return False, f"Modelo '{model}' não disponível"

    return True, None


def validate_user_credentials(username: str,
                              password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate user credentials format.

    Parameters
    ----------
    username : str
        Username to validate
    password : str
        Password to validate

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_message)
    """
    if not username or not username.strip():
        return False, "Nome de usuário é obrigatório"

    if not password:
        return False, "Senha é obrigatória"

    username = username.strip()

    # Username format validation
    if len(username) < 3:
        return False, "Nome de usuário deve ter pelo menos 3 caracteres"

    if len(username) > 50:
        return False, "Nome de usuário deve ter no máximo 50 caracteres"

    # Password format validation
    if len(password) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres"

    # Username pattern check (alphanumeric, underscore, hyphen)
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return False, ("Nome de usuário deve conter apenas letras, "
                       "números, _ ou -")

    return True, None


def validate_text_content(content: str) -> Tuple[bool, Optional[str]]:
    """
    Validate generated text content.

    Parameters
    ----------
    content : str
        Text content to validate

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_message)
    """
    if not content or not content.strip():
        return False, "Conteúdo do texto não pode estar vazio"

    content = content.strip()

    # Minimum content length
    if len(content) < 50:
        return False, "Texto deve ter pelo menos 50 caracteres"

    # Maximum content length (adjust based on requirements)
    if len(content) > 10000:
        return False, "Texto excede o tamanho máximo permitido"

    # Check for suspicious patterns
    suspicious_patterns = [
        r"<script.*?>",
        r"javascript:",
        r"<iframe.*?>",
        r"eval\s*\(",
        r"document\.cookie"
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return False, "Conteúdo contém elementos não permitidos"

    return True, None


def validate_search_query(query: str) -> Tuple[bool, Optional[str]]:
    """
    Validate search query input.

    Parameters
    ----------
    query : str
        Search query to validate

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_message)
    """
    if not query or not query.strip():
        return False, "Consulta de busca é obrigatória"

    query = query.strip()

    # Minimum query length
    if len(query) < 2:
        return False, "Consulta deve ter pelo menos 2 caracteres"

    # Maximum query length
    if len(query) > 200:
        return False, "Consulta deve ter no máximo 200 caracteres"

    return True, None


def validate_pagination_params(page: int,
                               page_size: int) -> Tuple[bool, Optional[str]]:
    """
    Validate pagination parameters.

    Parameters
    ----------
    page : int
        Page number
    page_size : int
        Number of items per page

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_message)
    """
    if page < 1:
        return False, "Número da página deve ser maior que 0"

    if page_size < 1:
        return False, "Tamanho da página deve ser maior que 0"

    if page_size > 100:
        return False, "Tamanho da página deve ser no máximo 100"

    return True, None


def validate_text_filters(filters: Dict[str, Any]) -> Tuple[
        bool, Optional[str]]:
    """
    Validate text filtering parameters.

    Parameters
    ----------
    filters : Dict[str, Any]
        Filter parameters

    Returns
    -------
    Tuple[bool, Optional[str]]
        (is_valid, error_message)
    """
    allowed_status = ["Todos", "Aprovados", "Pendentes", "Negados"]

    status = filters.get("status")
    if status and status not in allowed_status:
        return False, f"Status deve ser um de: {', '.join(allowed_status)}"

    search = filters.get("search")
    if search:
        is_valid, error_msg = validate_search_query(search)
        if not is_valid:
            return False, f"Busca: {error_msg}"

    return True, None


def validate_environment_config() -> Tuple[bool, List[str]]:
    """
    Validate essential environment configuration.

    Returns
    -------
    Tuple[bool, List[str]]
        (is_valid, list_of_missing_configs)
    """
    from config.settings import settings

    missing_configs = []

    # Check required configurations
    required_configs = [
        ("django_api_url", settings.django_api_url),
        ("elasticsearch_url", settings.elasticsearch_url),
        ("redis_url", settings.redis_url),
        ("secret_key", settings.secret_key)
    ]

    for config_name, config_value in required_configs:
        if not config_value or config_value == f"your_{config_name}_here":
            missing_configs.append(config_name)

    return len(missing_configs) == 0, missing_configs
