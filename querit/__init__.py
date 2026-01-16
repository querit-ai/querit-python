"""
Querit public API.

This module defines the public interface of the Querit package,
exposing the main client class and package version information.
"""

from querit.client import QueritClient
from querit.version import __version__

__all__ = ["QueritClient", "__version__"]
