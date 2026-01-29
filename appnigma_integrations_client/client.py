"""Main client class for Appnigma Integrations API."""

import asyncio
import os
import logging
from typing import Optional, Any, Dict
import aiohttp
from aiohttp import ClientError, ClientTimeout

from .errors import AppnigmaAPIError
from .types import ConnectionCredentials, SalesforceProxyRequest, ListConnectionsResponse

SDK_VERSION = '0.1.3'
DEFAULT_BASE_URL = 'https://integrations.appnigma.ai'
DEFAULT_TIMEOUT = 30.0  # 30 seconds

logger = logging.getLogger(__name__)


class AppnigmaClient:
    """Official Python SDK for Appnigma Integrations API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        debug: bool = False
    ):
        """
        Initialize AppnigmaClient.

        Args:
            api_key: API key for authentication. If not provided, will read from
                     APPNIGMA_API_KEY environment variable.
            base_url: Base URL for the API. Defaults to https://integrations.appnigma.ai
            debug: Enable debug logging of requests and responses.

        Raises:
            ValueError: If API key is not provided and APPNIGMA_API_KEY environment
                       variable is not set.
        """
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.getenv('APPNIGMA_API_KEY', '')

        if not self.api_key:
            raise ValueError(
                'API key is required. Provide it in the constructor or set '
                'APPNIGMA_API_KEY environment variable.'
            )

        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip('/')
        self.debug = debug

        # Configure logging
        if debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format='[Appnigma SDK] %(message)s'
            )

        # Create aiohttp session (will be created lazily)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp ClientSession for connection pooling."""
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=DEFAULT_TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self):
        """Close the aiohttp session. Call this when done with the client."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def list_connections(
        self,
        integration_id: Optional[str] = None,
        environment: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> ListConnectionsResponse:
        """
        List connections for the integration (integration from API key or integration_id).

        Args:
            integration_id: Optional integration ID. Required if API key is not
                            integration-scoped.
            environment: Optional filter (e.g. production, sandbox).
            status: Optional filter (e.g. connected).
            search: Optional search on user email.
            limit: Optional page size (default 20).
            cursor: Optional pagination cursor from previous response.

        Returns:
            ListConnectionsResponse with connections, totalCount, and optional nextCursor.

        Raises:
            AppnigmaAPIError: If the API request fails
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': f'Appnigma-Integrations-Client-Python/{SDK_VERSION}'
        }

        if integration_id:
            headers['X-Integration-Id'] = integration_id

        params: Dict[str, str] = {}
        if environment is not None:
            params['environment'] = environment
        if status is not None:
            params['status'] = status
        if search is not None:
            params['search'] = search
        if limit is not None:
            params['limit'] = str(limit)
        if cursor is not None:
            params['cursor'] = cursor

        url = f'{self.base_url}/api/v1/connections'
        if params:
            from urllib.parse import urlencode
            url = f'{url}?{urlencode(params)}'

        if self.debug:
            self._log_request('GET', url, headers, None)

        try:
            session = await self._get_session()
            async with session.get(url, headers=headers) as response:
                status = response.status
                data = await response.json()

                if self.debug:
                    self._log_response('GET', url, status, data)

                if status >= 200 and status < 300:
                    return data
                else:
                    raise self._create_error(status, data, 'GET', url)

        except ClientError as e:
            raise self._handle_network_error(e, 'GET', url)
        except Exception as e:
            if isinstance(e, AppnigmaAPIError):
                raise
            raise AppnigmaAPIError(
                0,
                'UnknownError',
                f'Unexpected error: {str(e)}',
                None
            )

    async def get_connection_credentials(
        self,
        connection_id: str,
        integration_id: Optional[str] = None
    ) -> ConnectionCredentials:
        """
        Get connection credentials (access token and metadata).

        Args:
            connection_id: The connection ID
            integration_id: Optional integration ID. Required if API key is not
                           integration-scoped.

        Returns:
            Connection credentials dictionary

        Raises:
            AppnigmaAPIError: If the API request fails
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': f'Appnigma-Integrations-Client-Python/{SDK_VERSION}'
        }

        if integration_id:
            headers['X-Integration-Id'] = integration_id

        url = f'{self.base_url}/api/v1/connections/{connection_id}/credentials'

        if self.debug:
            self._log_request('GET', url, headers, None)

        try:
            session = await self._get_session()
            async with session.get(url, headers=headers) as response:
                status = response.status
                data = await response.json()

                if self.debug:
                    self._log_response('GET', url, status, data)

                if status >= 200 and status < 300:
                    return data
                else:
                    raise self._create_error(status, data, 'GET', url)

        except ClientError as e:
            raise self._handle_network_error(e, 'GET', url)
        except Exception as e:
            if isinstance(e, AppnigmaAPIError):
                raise
            raise AppnigmaAPIError(
                0,
                'UnknownError',
                f'Unexpected error: {str(e)}',
                None
            )

    async def proxy_salesforce_request(
        self,
        connection_id: str,
        request_data: SalesforceProxyRequest,
        integration_id: Optional[str] = None
    ) -> Any:
        """
        Proxy a Salesforce API request.

        Args:
            connection_id: The connection ID to use
            request_data: Request data (method, path, query, data)
            integration_id: Optional integration ID. Required if API key is not
                           integration-scoped.

        Returns:
            Raw Salesforce API response (unparsed)

        Raises:
            AppnigmaAPIError: If the API request fails
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-Connection-Id': connection_id,
            'User-Agent': f'Appnigma-Integrations-Client-Python/{SDK_VERSION}'
        }

        if integration_id:
            headers['X-Integration-Id'] = integration_id

        url = f'{self.base_url}/api/v1/proxy/salesforce'

        if self.debug:
            self._log_request('POST', url, headers, request_data)

        try:
            session = await self._get_session()
            async with session.post(url, headers=headers, json=request_data) as response:
                status = response.status
                data = await response.json()

                if self.debug:
                    self._log_response('POST', url, status, data)

                if status >= 200 and status < 300:
                    return data
                else:
                    raise self._create_error(status, data, 'POST', url)

        except ClientError as e:
            raise self._handle_network_error(e, 'POST', url)
        except Exception as e:
            if isinstance(e, AppnigmaAPIError):
                raise
            raise AppnigmaAPIError(
                0,
                'UnknownError',
                f'Unexpected error: {str(e)}',
                None
            )

    def _create_error(
        self,
        status_code: int,
        response_data: Any,
        method: str,
        url: str
    ) -> AppnigmaAPIError:
        """Create AppnigmaAPIError from response data."""
        if isinstance(response_data, dict):
            error = response_data.get('error', 'APIError')
            message = response_data.get('message', f'API request failed with status {status_code}')
        else:
            error = 'APIError'
            message = f'API request failed with status {status_code}'

        return AppnigmaAPIError(status_code, error, message, response_data)

    def _handle_network_error(
        self,
        error: Exception,
        method: str,
        url: str
    ) -> AppnigmaAPIError:
        """Handle network errors and convert to AppnigmaAPIError."""
        error_msg = str(error)

        if 'timeout' in error_msg.lower() or isinstance(error, asyncio.TimeoutError):
            return AppnigmaAPIError(
                0,
                'NetworkError',
                f'Request timeout: {method} {url} exceeded {DEFAULT_TIMEOUT}s',
                None
            )

        if 'connection' in error_msg.lower() or 'resolve' in error_msg.lower():
            return AppnigmaAPIError(
                0,
                'NetworkError',
                f'Connection failed: Unable to reach {url}',
                None
            )

        return AppnigmaAPIError(
            0,
            'NetworkError',
            f'Network error: {error_msg}',
            None
        )

    def _log_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Any]
    ):
        """Log request details (with API key redaction)."""
        redacted_headers = headers.copy()
        if 'Authorization' in redacted_headers:
            redacted_headers['Authorization'] = 'Bearer ***'

        logger.debug(f'{method} {url}')
        logger.debug(f'Headers: {redacted_headers}')
        if body:
            logger.debug(f'Request Body: {body}')

    def _log_response(self, method: str, url: str, status: int, body: Any):
        """Log response details."""
        logger.debug(f'{method} {url} - Status: {status}')
        logger.debug(f'Response Body: {body}')
