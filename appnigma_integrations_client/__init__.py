"""Official Python SDK for Appnigma Integrations API."""

from .client import AppnigmaClient
from .errors import AppnigmaAPIError
from .types import ConnectionCredentials, ConnectionSummary, ListConnectionsResponse, SalesforceProxyRequest

__version__ = '0.1.3'
__all__ = [
    'AppnigmaClient',
    'AppnigmaAPIError',
    'ConnectionCredentials',
    'ConnectionSummary',
    'ListConnectionsResponse',
    'SalesforceProxyRequest'
]
