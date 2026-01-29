"""Official Python SDK for Appnigma Integrations API."""

from .client import AppnigmaClient
from .errors import AppnigmaAPIError
from .types import ConnectionCredentials, SalesforceProxyRequest

__version__ = '0.1.2'
__all__ = [
    'AppnigmaClient',
    'AppnigmaAPIError',
    'ConnectionCredentials',
    'SalesforceProxyRequest'
]
