"""
Querit Search API Python Client.

This module provides a typed Python client for the Querit Search API. It allows
you to construct search requests, send them to the Querit service, and receive
structured responses.
"""
from typing import Dict, Any, Optional

from querit.models.request import SearchRequest
from querit.models.response import SearchResponse
from querit.utils.http import post_json


class QueritClient:
    """
    Querit Search API Client
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.querit.ai",
        base_path: str = "/v1/search",
        timeout: float = 60.0,
        proxies: Optional[Dict[str, str]] = None,
    ):
        """Initializes the QueritClient.

        Args:
            api_key (str):
                Querit API key used for authentication. Required.
            base_url (str, optional):
                Base API endpoint URL. Defaults to "https://api.querit.ai".
            base_path (str, optional):
                Search API path. Defaults to "/v1/search".
            timeout (float, optional):
                HTTP request timeout in seconds. Defaults to 60.0.
            proxies (Dict[str, str], optional):
                Proxy configuration for HTTP(S) requests. Example:
                {
                    "http": "http://127.0.0.1:7890",
                    "https": "http://127.0.0.1:7890"
                }

        Raises:
            ValueError:
                If api_key is missing or empty.
        """
        if not api_key:
            raise ValueError("An API key must be provided")

        self.url = base_url.rstrip("/") + base_path
        self.timeout = timeout
        self.proxies = proxies

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def search(self, request: SearchRequest) -> SearchResponse:
        """
        Perform a search request.

        Args:
            request (SearchRequest): Search request model.

        Returns:
            SearchResponse: Typed search response.
        
        Example:
            client = QueritClient(api_key="xxx")

            req = SearchRequest(
                query="chat",
                count=5,
            )

            response = client.search(req)
        """

        raw = post_json(
            url=self.url,
            headers=self.headers,
            payload=request.to_payload(),
            timeout=self.timeout,
            proxies=self.proxies,
        )

        return SearchResponse(raw)
