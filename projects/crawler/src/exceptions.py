# -*- coding: utf-8 -*-
"""
Custom Exceptions for Crawler
"""


class CrawlerError(Exception):
    """Base exception for all crawler errors"""
    pass


class NetworkError(CrawlerError):
    """Network request related errors"""
    pass


class ParseError(CrawlerError):
    """HTML parsing related errors"""
    pass


class AuthenticationError(CrawlerError):
    """Authentication/authorization errors"""
    pass


class RateLimitError(CrawlerError):
    """Rate limiting errors (429 status)"""
    pass


class ConfigurationError(CrawlerError):
    """Configuration related errors"""
    pass


class ExportError(CrawlerError):
    """Content export related errors"""
    pass


class SiteNotSupportedError(CrawlerError):
    """Site not supported error"""
    pass


class ExtractionError(CrawlerError):
    """Content extraction errors"""
    pass


__all__ = [
    'CrawlerError',
    'NetworkError',
    'ParseError',
    'AuthenticationError',
    'RateLimitError',
    'ConfigurationError',
    'ExportError',
    'SiteNotSupportedError',
    'ExtractionError',
]
