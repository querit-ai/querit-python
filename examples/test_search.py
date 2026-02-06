"""
Querit Search API usage example.

This module demonstrates how to use QueritClient to construct a
SearchRequest with filters (language, geo, site, time range) and
execute a search request, then iterate over the returned results.
"""

from querit import QueritClient
from querit.models.request import (
    SearchRequest,
    SearchFilters,
    SiteFilter,
    GeoFilter,
)
from querit.utils import Language, Country

def main():
    """
    Run a simple Querit search example.

    This function initializes a QueritClient, builds a SearchRequest
    with query parameters and filters, sends the request to the Querit
    Search API, and prints URLs from the search results.
    """
    client = QueritClient(api_key="querit-sk-He0EyzZtlUaSdara-NcVkvUqwcg1ZihqW3dECSeFu0DmXAHF2")

    req = SearchRequest(
        query="chat",
        count=5,
        filters=SearchFilters(
            languages=[Language.ENGLISH],
            geo=GeoFilter(countries=[ Country.UNITED_STATES]),
            sites=SiteFilter(include=["dictionary.cambridge.org"]),
            time_range="m7",
        ),
    )

    try:
        response = client.search(req)
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    for item in response.results:
        print(item.url)


if __name__ == "__main__":
    main()
