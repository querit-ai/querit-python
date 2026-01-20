# Copyright 2025 QUERIT PRIVATE LIMITED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Querit Search API usage example.

This module demonstrates how to use QueritClient to construct a
SearchRequest with filters (language, geo, site, time range) and
execute a search request, then iterate over the returned results.
"""

from querit import QueritClient
from querit.models.request import (
    GeoFilter,
    SearchFilters,
    SearchRequest,
    SiteFilter,
)
from querit.utils import Country, Language


def main():
    """
    Run a simple Querit search example.

    This function initializes a QueritClient, builds a SearchRequest
    with query parameters and filters, sends the request to the Querit
    Search API, and prints URLs from the search results.
    """
    client = QueritClient(api_key="YOUR_API_KEY")

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

    response = client.search(req)

    for item in response.results:
        print(item.url)


if __name__ == "__main__":
    main()
