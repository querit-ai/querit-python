"""
Search request data models and filter definitions.

This module defines a set of dataclasses used to construct structured
search request payloads, including site filters, geographic filters,
and other query constraints. Each model provides a helper method to
convert itself into a dictionary representation suitable for API requests.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union
from querit.utils import Language
from querit.utils import Country


LanguageLike = Union[Language, str]
CountryLike = Union[Country, str]

def _normalize_language(lang: LanguageLike) -> str:
    """
    Normalize language input to its string representation.

    Accepts either a Language enum or a string. String values are validated
    against the Language enum.

    Raises:
        ValueError: If the language string is not supported.
        TypeError: If the language type is invalid.
    """
    if isinstance(lang, Language):
        return lang.value

    if isinstance(lang, str):
        try:
            return Language(lang).value
        except ValueError:
            raise ValueError(f"Unsupported language: {lang}")

    raise TypeError(f"Invalid language type: {type(lang)}")


def _normalize_country(country: CountryLike) -> str:
    """
    Normalize country input to its string representation.
    """
    if isinstance(country, Country):
        return country.value

    if isinstance(country, str):
        try:
            return Country(country).value
        except ValueError:
            raise ValueError(f"Unsupported country: {country}")

    raise TypeError(f"Invalid country type: {type(country)}")


@dataclass
class SiteFilter:
    """
    Site-level filter configuration.

    Used to explicitly include or exclude specific sites from search
    results. This is commonly used for whitelist/blacklist behavior.

    Attributes:
        include (Optional[List[str]]):
            A list of site domains that must be included in results.
            If None, no explicit inclusion filtering is applied.

        exclude (Optional[List[str]]):
            A list of site domains that must be excluded from results.
            If None, no exclusion filtering is applied.

    Notes:
        - Both include and exclude may be defined at the same time.
        - If both are None or empty, the filter is considered inactive.
    """

    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the site filter configuration into a dictionary.

        Returns:
            Dict[str, Any]:
                A dictionary describing the site-based filtering rules.
                Returns an empty dictionary if no rules are defined.
        """
        data = {}
        if self.include:
            data["include"] = self.include
        if self.exclude:
            data["exclude"] = self.exclude
        return data


@dataclass
class GeoFilter:
    """
    Geographic filter configuration.

    Used to restrict search results to specific countries.

    Attributes:
        countries (Optional[List[CountryLike]]):
           Country filter specifying which countries to include in the results.
    """

    countries: Optional[List[CountryLike]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the geographic filter configuration into a dictionary.

        Returns:
            Dict[str, Any]:
                A dictionary formatted for API consumption containing
                country inclusion rules. Returns an empty dictionary if
                no countries are specified.
        """
        if not self.countries:
            return {}
        return {
            "countries": {
                "include": [
                   _normalize_country(country)
                   for country in self.countries
               ]
            }
        }


@dataclass
class SearchFilters:
    """
    Composite search filter configuration.

    Encapsulates language, geographic, site, and time range filters that
    together define the constraints applied to a search request.

    Attributes:
        languages (Optional[List[LanguageLike]]):
            The search language preference.

        geo (Optional[GeoFilter]):
            Geolocation-based filtering.

        sites (Optional[SiteFilter]):
            Site filtering, specify which websites to include or exclude in the results.

        time_range (Optional[str]):
            Time range filtering, specify the date or time period for the results.

    """

    languages: Optional[List[LanguageLike]] = None
    geo: Optional[GeoFilter] = None
    sites: Optional[SiteFilter] = None
    time_range: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert all defined search filters into a dictionary.

        Returns:
            Dict[str, Any]:
                A dictionary representing all active filters. If no filters
                are defined, returns an empty dictionary.
        """
        filters = {}

        if self.languages:
            filters["languages"] = {
                "include": [
                   _normalize_language(lang)
                   for lang in self.languages
               ]
            }

        if self.geo:
            geo_dict = self.geo.to_dict()
            if geo_dict:
                filters["geo"] = geo_dict

        if self.sites:
            site_dict = self.sites.to_dict()
            if site_dict:
                filters["sites"] = site_dict

        if self.time_range:
            filters["timeRange"] = {"date": self.time_range}

        return filters


@dataclass
class SearchRequest:
    """
    Search request model.

    Represents a complete search request including the query text,
    pagination settings, and optional advanced filters.

    Attributes:
        query (str):
            The search query text. This field is required.

        count (int):
            The maximum number of results to return.

        filters (Optional[SearchFilters]):
            Filter conditions, used to further refine the search results.

    """

    query: str
    count: int = 10
    filters: Optional[SearchFilters] = None

    def to_payload(self) -> Dict[str, Any]:
        """
        Convert the search request into a payload dictionary.

        Returns:
            Dict[str, Any]:
                A dictionary payload containing the query, result count,
                and any active filter rules. This structure is suitable
                for direct submission to a search API.
        """
        payload = {
            "query": self.query,
            "count": self.count,
        }

        if self.filters:
            filters_dict = self.filters.to_dict()
            if filters_dict:
                payload["filters"] = filters_dict

        return payload