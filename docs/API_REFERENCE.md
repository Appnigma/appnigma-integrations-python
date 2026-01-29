# API Reference

Complete reference documentation for the Appnigma Integrations Python SDK.

## Table of Contents

- [AppnigmaClient](#appnigmaclient)
- [Types](#types)
- [Errors](#errors)

## AppnigmaClient

The main client class for interacting with the Appnigma Integrations API.

### Constructor

```python
AppnigmaClient(api_key=None, base_url=None, debug=False)
```

Creates a new client instance.

#### Parameters

- `api_key` (optional, str): API key for authentication. If not provided, reads from `APPNIGMA_API_KEY` environment variable.
- `base_url` (optional, str): Base URL for the API. Defaults to `https://integrations.appnigma.ai`.
- `debug` (optional, bool): Enable debug logging. Defaults to `False`.

#### Raises

- `ValueError`: If API key is not provided and `APPNIGMA_API_KEY` environment variable is not set.

#### Example

```python
client = AppnigmaClient(
    api_key='your-api-key',
    base_url='https://integrations.appnigma.ai',
    debug=False
)
```

### Methods

#### `get_connection_credentials(connection_id, integration_id=None)`

Retrieves decrypted access token and metadata for a Salesforce connection.

**Signature:**
```python
async def get_connection_credentials(
    connection_id: str,
    integration_id: Optional[str] = None
) -> ConnectionCredentials
```

**Parameters:**
- `connection_id` (str, required): The connection ID to retrieve credentials for
- `integration_id` (str, optional): Integration ID. Automatically extracted from API key if not provided.

**Returns:** `ConnectionCredentials` (TypedDict)

**Raises:** `AppnigmaAPIError` if the API request fails

**Example:**
```python
credentials = await client.get_connection_credentials('conn-123')

print('Access Token:', credentials['accessToken'])
print('Instance URL:', credentials['instanceUrl'])
print('Expires At:', credentials['expiresAt'])
```

**Response Structure:**
```python
{
    'accessToken': str,      # Salesforce access token
    'instanceUrl': str,      # Salesforce instance URL (e.g., https://na1.salesforce.com)
    'environment': str,      # "production" or "sandbox"
    'region': str,           # Geographic region code (e.g., "NA", "EU")
    'tokenType': str,        # Usually "Bearer"
    'expiresAt': str         # ISO 8601 timestamp when token expires
}
```

**Error Codes:**
- `400`: Bad Request - Invalid connection ID or connection not in 'connected' status
- `401`: Unauthorized - Invalid or revoked API key
- `403`: Forbidden - API key doesn't match integration or connection doesn't belong to integration
- `404`: Not Found - Connection, Integration, or Company not found
- `500`: Internal Server Error - Server error or token refresh failure

#### `proxy_salesforce_request(connection_id, request_data, integration_id=None)`

Makes a proxied API call to Salesforce with automatic token refresh and usage tracking.

**Signature:**
```python
async def proxy_salesforce_request(
    connection_id: str,
    request_data: SalesforceProxyRequest,
    integration_id: Optional[str] = None
) -> Any
```

**Parameters:**
- `connection_id` (str, required): The connection ID to use for the API call
- `request_data` (SalesforceProxyRequest, required): Request configuration dictionary
  - `method` (required, str): HTTP method - 'GET', 'POST', 'PUT', 'PATCH', or 'DELETE'
  - `path` (required, str): Salesforce API path (e.g., '/services/data/v59.0/query')
  - `query` (optional, dict): Query parameters as key-value pairs (for GET requests)
  - `data` (optional, any): Request body data (for POST, PUT, PATCH requests)
- `integration_id` (str, optional): Integration ID. Automatically extracted from API key if not provided.

**Returns:** Raw Salesforce API response (dict, list, or other JSON-serializable type)

**Raises:** `AppnigmaAPIError` if the API request fails

**Example:**
```python
# GET request with query parameters
response = await client.proxy_salesforce_request('conn-123', {
    'method': 'GET',
    'path': '/services/data/v59.0/query',
    'query': {
        'q': 'SELECT Id, Name FROM Account LIMIT 10'
    }
})

# POST request with body data
new_record = await client.proxy_salesforce_request('conn-123', {
    'method': 'POST',
    'path': '/services/data/v59.0/sobjects/Contact',
    'data': {
        'FirstName': 'John',
        'LastName': 'Doe',
        'Email': 'john@example.com'
    }
})
```

**Features:**
- Automatic token refresh if the access token is expired or about to expire
- Usage tracking for billing purposes
- Error handling and retries for transient failures

**Error Codes:**
- `400`: Bad Request - Invalid request parameters or connection not in 'connected' status
- `401`: Unauthorized - Invalid or revoked API key
- `403`: Forbidden - API key doesn't match integration or connection doesn't belong to integration
- `404`: Not Found - Connection, Integration, or Company not found
- `429`: Too Many Requests - Monthly rate limit exceeded (includes `planLimit`, `currentUsage`, `offerings` in error details)
- `500`: Internal Server Error - Server error, token refresh failure, or Salesforce API error

#### `close()`

Closes the aiohttp session. Call this when done with the client, or use the async context manager.

**Signature:**
```python
async def close() -> None
```

**Example:**
```python
client = AppnigmaClient(api_key='your-api-key')
try:
    # Use client
    await client.get_connection_credentials('connection-id')
finally:
    await client.close()
```

### Async Context Manager

The client supports async context managers for automatic resource cleanup:

```python
async with AppnigmaClient(api_key='your-api-key') as client:
    credentials = await client.get_connection_credentials('connection-id')
    # Client is automatically closed when exiting the context
```

## Types

### ConnectionCredentials

Response structure for connection credentials.

```python
class ConnectionCredentials(TypedDict):
    accessToken: str      # Salesforce access token
    instanceUrl: str       # Salesforce instance URL
    environment: str       # "production" or "sandbox"
    region: str            # Geographic region code
    tokenType: str         # Usually "Bearer"
    expiresAt: str          # ISO 8601 expiration timestamp
```

### SalesforceProxyRequest

Request data for proxying Salesforce API calls.

```python
class SalesforceProxyRequest(TypedDict):
    method: Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
    path: str
    query: NotRequired[Optional[Dict[str, Any]]]  # Optional query parameters
    data: NotRequired[Optional[Any]]              # Optional request body
```

## Errors

### AppnigmaAPIError

Custom exception class for API errors.

```python
class AppnigmaAPIError(Exception):
    status_code: int          # HTTP status code
    error: str                # Error type/code
    message: str              # Human-readable error message
    response_body: Optional[Any]  # Full response body from API
```

#### Properties

- `status_code` (int): HTTP status code from the API response
- `error` (str): Error type/code from the API response
- `message` (str): Human-readable error message
- `response_body` (any, optional): Full response body from the API

#### Methods

##### `get_details()`

Returns error details including rate limit information if available.

**Signature:**
```python
def get_details() -> dict
```

**Returns:** Dictionary with error details

**Example:**
```python
try:
    await client.proxy_salesforce_request('conn-123', { /* ... */ })
except AppnigmaAPIError as e:
    if e.status_code == 429:
        details = e.get_details()
        print('Plan Limit:', details.get('planLimit'))
        print('Current Usage:', details.get('currentUsage'))
        print('Offerings:', details.get('offerings'))
```

### Error Handling Best Practices

1. **Always check error type**: Use `isinstance(error, AppnigmaAPIError)` to distinguish API errors from other errors
2. **Handle rate limits**: Check for `429` status code and use `get_details()` to get rate limit information
3. **Log error details**: Include `status_code`, `error`, and `message` in your error logs
4. **Retry logic**: Implement retry logic for transient errors (5xx status codes)
5. **User-friendly messages**: Translate technical error messages to user-friendly messages

**Example:**
```python
async def make_request_with_retry(connection_id: str, max_retries: int = 3):
    for attempt in range(1, max_retries + 1):
        try:
            return await client.proxy_salesforce_request(connection_id, { /* ... */ })
        except AppnigmaAPIError as e:
            # Don't retry client errors (4xx)
            if 400 <= e.status_code < 500:
                raise
            
            # Retry server errors (5xx)
            if attempt == max_retries:
                raise
            
            # Exponential backoff
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            raise
```

## Rate Limiting

The API implements two layers of rate limiting:

1. **Per-minute rate limiting**: 100 requests per minute (configurable)
2. **Monthly rate limiting**: Based on your company's subscribed offerings

When rate limits are exceeded, the API returns a `429 Too Many Requests` error with details about your plan limits and current usage.

**Rate Limit Headers:**
All responses include rate limit information:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in the current window
- `X-RateLimit-Reset`: Timestamp when the rate limit resets

**Handling Rate Limits:**
```python
try:
    await client.proxy_salesforce_request('conn-123', { /* ... */ })
except AppnigmaAPIError as e:
    if e.status_code == 429:
        details = e.get_details()
        print(f"Rate limit exceeded. Plan limit: {details.get('planLimit')}, "
              f"Current usage: {details.get('currentUsage')}")
        # Implement exponential backoff or notify user
```

## Type Hints

The SDK includes complete type hints for better IDE support:

```python
from typing import Dict, List, Any
from appnigma_integrations_client import AppnigmaClient, ConnectionCredentials

async def get_credentials(
    client: AppnigmaClient,
    connection_id: str
) -> ConnectionCredentials:
    return await client.get_connection_credentials(connection_id)

async def query_accounts(
    client: AppnigmaClient,
    connection_id: str
) -> Dict[str, Any]:
    return await client.proxy_salesforce_request(connection_id, {
        'method': 'GET',
        'path': '/services/data/v59.0/query',
        'query': {'q': 'SELECT Id, Name FROM Account LIMIT 10'}
    })
```

## Async/Await Pattern

All SDK methods are coroutines and must be used with `async`/`await`:

```python
import asyncio
from appnigma_integrations_client import AppnigmaClient

async def main():
    async with AppnigmaClient(api_key='your-api-key') as client:
        # All methods are async
        credentials = await client.get_connection_credentials('connection-id')
        response = await client.proxy_salesforce_request('connection-id', {
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {'q': 'SELECT Id FROM Account LIMIT 10'}
        })
        print(response)

# Run the async function
asyncio.run(main())
```

## Resource Management

Always close the client when done to free up resources:

```python
# Option 1: Explicit close
client = AppnigmaClient(api_key='your-api-key')
try:
    await client.get_connection_credentials('connection-id')
finally:
    await client.close()

# Option 2: Async context manager (recommended)
async with AppnigmaClient(api_key='your-api-key') as client:
    await client.get_connection_credentials('connection-id')
# Client is automatically closed
```
