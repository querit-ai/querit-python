"""
Search response data models.

This module defines response wrapper classes for search API results.
It provides structured access to raw response data through typed
properties, improving readability and safety when consuming search
results.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SearchResultItem:
    """
    Wrapper for a single search result item.

    Provides convenient property accessors for commonly used
    fields in a search result.
    """

    raw: Any

    @property
    def url(self) -> Optional[str]:
        """
        Get the URL of the search result.

        Returns:
            Optional[str]: The result URL, or None if unavailable.
        """
        return self.raw.get("url") if isinstance(self.raw, dict) else None

    @property
    def title(self) -> Optional[str]:
        """
        Get the title of the search result.

        Returns:
            Optional[str]: The result title, or None if unavailable.
        """
        return self.raw.get("title") if isinstance(self.raw, dict) else None

    @property
    def snippet(self) -> Optional[str]:
        """
        Get the text snippet of the search result.

        Returns:
            Optional[str]: The result snippet, or None if unavailable.
        """
        return self.raw.get("snippet") if isinstance(self.raw, dict) else None

    @property
    def page_time(self) -> Optional[int]:
        """
        Get the page publish timestamp.

        Returns:
            Optional[int]: Page time as a timestamp, or None if unavailable.
        """
        return self.raw.get("page_time") if isinstance(self.raw, dict) else None

    @property
    def page_age(self) -> Optional[str]:
        """
        Get the page age description.

        Returns:
            Optional[str]: Page age (e.g., relative time), or None if unavailable.
        """
        return self.raw.get("page_age") if isinstance(self.raw, dict) else None

    @property
    def site_display_type(self) -> Optional[int]:
        """
        Get the site display type.

        Returns:
            Optional[int]: Site display type identifier, or None if unavailable.
        """
        return self.raw.get("site_display_type") if isinstance(self.raw, dict) else None

    @property
    def language(self) -> Optional[int]:
        """
        Get the language identifier of the result.

        Returns:
            Optional[int]: Language code, or None if unavailable.
        """
        return self.raw.get("language") if isinstance(self.raw, dict) else None

    @property
    def site_auth_level(self) -> Optional[int]:
        """
        Get the site authority level.

        Returns:
            Optional[int]: Site authority level, or None if unavailable.
        """
        return self.raw.get("site_auth_level") if isinstance(self.raw, dict) else None

    @property
    def page_images(self) -> Optional[Dict[str, Any]]:
        """
        Get image information associated with the page.

        Returns:
            Optional[Dict[str, Any]]: Page image metadata, or None if unavailable.
        """
        return self.raw.get("page_images") if isinstance(self.raw, dict) else None


@dataclass
class SearchResponse:
    """
    Wrapper for a search API response.

    Provides structured access to response metadata and result items.
    """

    raw: Any

    @property
    def error_code(self) -> Optional[int]:
        """
        Get the error code from the response.

        Returns:
            Optional[int]: Error code, or None if not present.
        """
        if isinstance(self.raw, dict):
            return self.raw.get("error_code")
        return None

    @property
    def error_msg(self) -> Optional[str]:
        """
        Get the error message from the response.

        Returns:
            Optional[str]: Error message, or None if not present.
        """
        if isinstance(self.raw, dict):
            return self.raw.get("error_msg")
        return None

    @property
    def search_id(self) -> Optional[int]:
        """
        Get the unique search request ID.

        Returns:
            Optional[int]: Search ID, or None if not present.
        """
        if isinstance(self.raw, dict):
            return self.raw.get("search_id")
        return None

    @property
    def results(self) -> List[SearchResultItem]:
        """
        Get the list of search result items.

        Returns:
            List[SearchResultItem]: Parsed list of search result items.
                                    Empty list if no results are available.
        """
        items = []
        if isinstance(self.raw, dict):
            results = self.raw.get("results") or {}
            raw_items = results.get("result") if isinstance(results, dict) else []
            if isinstance(raw_items, list):
                items = raw_items
        return [SearchResultItem(item) for item in items]
