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
