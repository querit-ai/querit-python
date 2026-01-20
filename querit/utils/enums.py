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
Enumerations for search query localization.

This module defines enums used to describe the language and country
context of a search query. They are typically used for internationalized
search, ranking, or content filtering logic.
"""

from enum import Enum


class Language(str, Enum):
    """
    Supported languages for search queries.

    The value of each enum member represents the normalized language
    identifier used internally by the system.
    """
    ENGLISH = "english"
    JAPANESE = "japanese"
    KOREAN = "korean"
    GERMAN = "german"
    FRENCH = "french"
    SPANISH = "spanish"
    PORTUGUESE = "portuguese"


class Country(str, Enum):
    """
    Supported countries or regions for search queries.

    The value of each enum member represents the normalized country
    identifier used internally by the system.
    """
    ARGENTINA = "argentina"
    AUSTRALIA = "australia"
    BRAZIL = "brazil"
    CANADA = "canada"
    COLOMBIA = "colombia"
    FRANCE = "france"
    GERMANY = "germany"
    INDIA = "india"
    INDONESIA = "indonesia"
    JAPAN = "japan"
    MEXICO = "mexico"
    NIGERIA = "nigeria"
    PHILIPPINES = "philippines"
    SOUTH_KOREA = "south korea"
    SPAIN = "spain"
    UNITED_KINGDOM = "united kingdom"
    UNITED_STATES = "united states"
