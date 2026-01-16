"""
HTTP utility functions.

This module provides low-level HTTP helpers used to send JSON-based
POST requests and map HTTP status codes to domain-specific exceptions.
"""

import json
import requests
from typing import Dict, Any, Optional

from ..errors import (
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    RateLimitError,
    ServerError,
)


def post_json(
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: float = 30.0,
    proxies: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Send a POST request with a JSON payload and return the parsed response.

    This function wraps `requests.post` to provide:
    - JSON serialization of request payloads
    - Timeout handling
    - Optional proxy support
    - Mapping of HTTP status codes to custom exceptions

    Args:
        url (str): Target request URL.
        headers (Dict[str, str]): HTTP headers to include in the request.
        payload (Dict[str, Any]): JSON-serializable request body.
        timeout (float, optional): Request timeout in seconds. Defaults to 30.0.
        proxies (Optional[Dict[str, str]]): Proxy configuration passed to requests.

    Returns:
        Dict[str, Any]: Parsed JSON response body.

    Raises:
        BadRequestError: If the server returns HTTP 400.
        UnauthorizedError: If the server returns HTTP 401.
        ForbiddenError: If the server returns HTTP 403.
        RateLimitError: If the server returns HTTP 429.
        ServerError: If a timeout occurs or an unexpected status code is returned.
    """
    try:
        resp = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=timeout,
            proxies=proxies,
        )
    except requests.exceptions.Timeout:
        raise ServerError("Request timeout")

    if resp.status_code == 200:
        return resp.json()

    if resp.status_code == 400:
        raise BadRequestError(resp.text)
    if resp.status_code == 401:
        raise UnauthorizedError(resp.text)
    if resp.status_code == 403:
        raise ForbiddenError(resp.text)
    if resp.status_code == 429:
        raise RateLimitError(resp.text)

    raise ServerError(
        f"Unexpected status: {resp.status_code}, body={resp.text}"
    )
