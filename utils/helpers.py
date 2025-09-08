"""
Helper utility functions for UniPOST application.

This module contains common utility functions used across
the application for formatting, processing, and general operations.
"""

import hashlib
from datetime import datetime
from typing import List


def format_date(date_str: str, format_type: str = "br") -> str:
    """
    Format date string to Brazilian format.

    Parameters
    ----------
    date_str : str
        ISO format date string
    format_type : str, optional
        Format type ("br" for Brazilian, "iso" for ISO)

    Returns
    -------
    str
        Formatted date string
    """
    try:
        if not date_str:
            return "N/A"

        # Parse ISO format
        date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

        if format_type == "br":
            return date_obj.strftime("%d/%m/%Y %H:%M")
        else:
            return date_obj.strftime("%Y-%m-%d %H:%M")

    except (ValueError, TypeError):
        return date_str


def truncate_text(
        text: str,
        max_length: int = 200,
        suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.

    Parameters
    ----------
    text : str
        Text to truncate
    max_length : int, optional
        Maximum length (default: 200)
    suffix : str, optional
        Suffix to add when truncated (default: "...")

    Returns
    -------
    str
        Truncated text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def generate_cache_key(prefix: str, *args) -> str:
    """
    Generate a cache key from prefix and arguments.

    Parameters
    ----------
    prefix : str
        Prefix for the cache key
    *args
        Arguments to include in the key

    Returns
    -------
    str
        Generated cache key
    """
    # Create a string from all arguments
    key_string = f"{prefix}:" + ":".join(str(arg) for arg in args)

    # Generate hash for long keys
    if len(key_string) > 100:
        hash_obj = hashlib.md5(key_string.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"

    return key_string


def sanitize_text(text: str) -> str:
    """
    Sanitize text for safe display and storage.

    Parameters
    ----------
    text : str
        Text to sanitize

    Returns
    -------
    str
        Sanitized text
    """
    if not text:
        return ""

    # Remove excessive whitespace
    text = " ".join(text.split())

    # Remove potentially harmful characters
    dangerous_chars = ["<script", "</script", "<iframe", "</iframe"]

    for char in dangerous_chars:
        text = text.replace(char, "")

    return text.strip()


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    Extract keywords from text for search and caching.

    Parameters
    ----------
    text : str
        Text to extract keywords from
    max_keywords : int, optional
        Maximum number of keywords (default: 5)

    Returns
    -------
    list
        List of extracted keywords
    """
    if not text:
        return []

    # Simple keyword extraction (could be improved with NLP)
    words = text.lower().split()

    # Remove common stop words (basic Portuguese)
    stop_words = {
        "a", "o", "e", "de", "do", "da", "em", "um", "uma", "com", "para",
        "por", "no", "na", "dos", "das", "que", "se", "não", "como", "mais",
        "mas", "ou", "muito", "bem", "já", "só", "também", "ainda", "onde"
    }

    # Filter words
    keywords = []
    for word in words:
        if (len(word) > 3 and
                word not in stop_words and
                word.isalpha() and
                word not in keywords):
            keywords.append(word)

        if len(keywords) >= max_keywords:
            break

    return keywords


def validate_jwt_token(token: str) -> bool:
    """
    Basic JWT token format validation.

    Parameters
    ----------
    token : str
        JWT token to validate

    Returns
    -------
    bool
        True if token format is valid, False otherwise
    """
    if not token:
        return False

    parts = token.split(".")
    return len(parts) == 3


def calculate_text_stats(text: str) -> dict:
    """
    Calculate basic statistics for text content.

    Parameters
    ----------
    text : str
        Text to analyze

    Returns
    -------
    dict
        Dictionary with text statistics
    """
    if not text:
        return {
            "characters": 0,
            "words": 0,
            "sentences": 0,
            "paragraphs": 0
        }

    characters = len(text)
    words = len(text.split())
    sentences = text.count(".") + text.count("!") + text.count("?")
    paragraphs = len([p for p in text.split("\n\n") if p.strip()])

    return {
        "characters": characters,
        "words": words,
        "sentences": sentences,
        "paragraphs": max(1, paragraphs)  # At least 1 paragraph
    }
