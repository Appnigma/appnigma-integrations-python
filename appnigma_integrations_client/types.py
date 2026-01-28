"""Type definitions for Appnigma Integrations Client."""

from typing import TypedDict, Literal, Optional, Any, Dict


class ConnectionCredentials(TypedDict):
    """Connection credentials response from the API."""
    accessToken: str
    instanceUrl: str
    environment: str
    region: str
    tokenType: str
    expiresAt: str


class SalesforceProxyRequest(TypedDict, total=False):
    """Request data for proxying Salesforce API calls."""
    method: Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    path: str
    query: Optional[Dict[str, Any]]
    data: Optional[Any]
