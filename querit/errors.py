"""
Custom exception definitions for Querit SDK.

This module defines the exception hierarchy used across the Querit SDK
to represent HTTP and server-side errors in a structured and explicit way.
"""


class QueritError(Exception):
    """
    Base exception for the Querit SDK.

    All custom exceptions raised by the SDK inherit from this class,
    allowing users to catch Querit-specific errors in a unified manner.
    """


class BadRequestError(QueritError):
    """
    Exception raised for HTTP 400 Bad Request errors.

    Indicates that the request parameters or payload are invalid.
    """


class UnauthorizedError(QueritError):
    """
    Exception raised for HTTP 401 Unauthorized errors.

    Indicates missing or invalid authentication credentials.
    """


class ForbiddenError(QueritError):
    """
    Exception raised for HTTP 403 Forbidden errors.

    Indicates that the client does not have permission to access
    the requested resource.
    """


class RateLimitError(QueritError):
    """
    Exception raised for HTTP 429 Too Many Requests errors.

    Indicates that the client has exceeded the allowed request rate.
    """


class ServerError(QueritError):
    """
    Exception raised for HTTP 5xx server errors.

    Indicates an internal server error or unexpected failure
    on the remote service.
    """
