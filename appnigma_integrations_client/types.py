"""Type definitions for Appnigma Integrations Client."""

from typing import TypedDict, Literal, Optional, Any, Dict

try:
    # Python 3.11+ has NotRequired in typing
    from typing import NotRequired
except ImportError:
    # For Python < 3.11, use typing_extensions
    try:
        from typing_extensions import NotRequired
    except ImportError:
        # Fallback: if typing_extensions is not available, we'll need to handle it differently
        # This shouldn't happen if dependencies are installed correctly
        raise ImportError(
            "typing_extensions is required for Python < 3.11. "
            "Install it with: pip install typing_extensions>=4.0.0"
        )


class ConnectionCredentials(TypedDict):
    """Connection credentials response from the API."""
    accessToken: str
    instanceUrl: str
    environment: str
    region: str
    tokenType: str
    expiresAt: str


class ConnectionSummary(TypedDict):
    """Summary of a connection (list response item)."""
    connectionId: str
    userEmail: str
    userName: str
    orgName: str
    environment: str
    region: str
    status: str
    connectedAt: str
    lastActiveAt: str


class ListConnectionsResponse(TypedDict):
    """Response from list connections API."""
    connections: list
    totalCount: int
    nextCursor: NotRequired[Optional[str]]


class SalesforceProxyRequest(TypedDict):
    """Request data for proxying Salesforce API calls."""
    method: Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    path: str
    query: NotRequired[Optional[Dict[str, Any]]]
    data: NotRequired[Optional[Any]]
