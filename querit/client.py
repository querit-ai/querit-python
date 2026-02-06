"""
Querit Search API Python Client.

This module provides a typed Python client for the Querit Search API. It allows
you to construct search requests, send them to the Querit service, and receive
structured responses.
"""
from typing import Dict, Any, Optional

import requests

from querit.models.request import SearchRequest
from querit.models.response import SearchResponse
from querit.utils.http import post_json, get_session


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
        session: Optional[requests.Session] = None,
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
            session (requests.Session, optional):
                If provided, this session will be used for all HTTP requests
                made by this client.
                If omitted, the client uses a shared global session created
                internally with the following default behavior:
                - Connection pooling enabled (up to 10 concurrent connections)
                - Automatic retries enabled for network-level failures only
                  (connection errors and read timeouts)
                - At most 1 retry attempt per request
                - POST requests are allowed to be retried
                - No automatic retries based on HTTP response status codes
                - Short exponential backoff between retries
                  (starting at approximately 50ms)
                - HTTP error responses are not raised automatically and are
                  handled explicitly by the client

        Raises:
            ValueError:
                If api_key is missing or empty.
        """
        if not api_key:
            raise ValueError("An API key must be provided")

        self.url = base_url.rstrip("/") + base_path
        self.timeout = timeout
        self.proxies = proxies
        self.session = session

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

        sess = self.session or get_session()

        raw = post_json(
            url=self.url,
            headers=self.headers,
            payload=request.to_payload(),
            timeout=self.timeout,
            proxies=self.proxies,
            session=sess,
        )

        return SearchResponse(raw)
