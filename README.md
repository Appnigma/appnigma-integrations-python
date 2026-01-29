# appnigma-integrations-client

Official Python SDK for the Appnigma Integrations API. This SDK provides a simple async interface for managing Salesforce connections and making proxied API calls to Salesforce.

## Installation

```bash
pip install appnigma-integrations-client
```

## Quick Start

```python
import asyncio
from appnigma_integrations_client import AppnigmaClient

async def main():
    # Initialize client
    client = AppnigmaClient(
        api_key='your-api-key'  # Optional if APPNIGMA_API_KEY is set
    )

    # Get connection credentials
    credentials = await client.get_connection_credentials(
        connection_id='connectionId',
        integration_id='integrationId'  # Optional - extracted from API key if not provided
    )

    # Make a proxied Salesforce API call
    response = await client.proxy_salesforce_request(
        connection_id='connectionId',
        request_data={
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {'q': 'SELECT Id, Name FROM Account LIMIT 10'}
        },
        integration_id='integrationId'  # Optional - extracted from API key if not provided
    )

    # Clean up
    await client.close()

asyncio.run(main())
```

### Using Async Context Manager

```python
import asyncio
from appnigma_integrations_client import AppnigmaClient

async def main():
    async with AppnigmaClient(api_key='your-api-key') as client:
        credentials = await client.get_connection_credentials('connectionId')
        response = await client.proxy_salesforce_request(
            'connectionId',
            {
                'method': 'GET',
                'path': '/services/data/v59.0/query',
                'query': {'q': 'SELECT Id, Name FROM Account LIMIT 10'}
            }
        )

asyncio.run(main())
```

## Authentication

The SDK supports two ways to provide your API key:

### Environment Variable (Recommended)

Set the `APPNIGMA_API_KEY` environment variable:

```bash
export APPNIGMA_API_KEY=your-api-key
```

Then initialize the client without providing the API key:

```python
client = AppnigmaClient()
```

### Explicit Configuration

Pass the API key directly in the constructor:

```python
client = AppnigmaClient(api_key='your-api-key')
```

**Note**: API keys are integration-scoped. The `integration_id` parameter is optional and will be automatically extracted from your API key if not provided.

## API Reference

### `AppnigmaClient`

Main client class for interacting with the Appnigma Integrations API.

#### Constructor

```python
AppnigmaClient(api_key=None, base_url=None, debug=False)
```

**Parameters:**
- `api_key` (optional): API key for authentication. Defaults to `APPNIGMA_API_KEY` environment variable.
- `base_url` (optional): Base URL for the API. Defaults to `https://integrations.appnigma.ai`.
- `debug` (optional): Enable debug logging. Defaults to `False`.

#### Methods

##### `get_connection_credentials(connection_id, integration_id=None)`

Retrieve decrypted access token and metadata for a Salesforce connection.

**Parameters:**
- `connection_id` (str, required): The connection ID
- `integration_id` (str, optional): Integration ID. Automatically extracted from API key if not provided.

**Returns:** `ConnectionCredentials` (TypedDict)

**Example:**
```python
credentials = await client.get_connection_credentials('conn-123', 'int-456')
print(credentials['accessToken'])
print(credentials['instanceUrl'])
```

**Response:**
```python
{
    'accessToken': str,
    'instanceUrl': str,
    'environment': str,
    'region': str,
    'tokenType': str,
    'expiresAt': str
}
```

##### `list_connections(integration_id=None, environment=None, status=None, search=None, limit=None, cursor=None)`

List connections for the integration (integration from API key).

**Parameters:**
- `integration_id` (optional): Integration ID. Extracted from API key if not provided.
- `environment`, `status`, `search`, `limit`, `cursor` (optional): Filters and pagination.

**Returns:** `ListConnectionsResponse` with `connections`, `totalCount`, `nextCursor` (optional)

**Example:**
```python
result = await client.list_connections(limit=10)
for conn in result['connections']:
    print(conn['connectionId'], conn['userEmail'])
```

##### `proxy_salesforce_request(connection_id, request_data, integration_id=None)`

Make a proxied API call to Salesforce with automatic token refresh and usage tracking.

**Parameters:**
- `connection_id` (str, required): The connection ID to use
- `request_data` (SalesforceProxyRequest, required): Request configuration
  - `method` (required): HTTP method - 'GET', 'POST', 'PUT', 'PATCH', or 'DELETE'
  - `path` (required): Salesforce API path (e.g., '/services/data/v59.0/query')
  - `query` (optional): Query parameters as key-value pairs
  - `data` (optional): Request body data (for POST, PUT, PATCH)
- `integration_id` (str, optional): Integration ID. Automatically extracted from API key if not provided.

**Returns:** Raw Salesforce API response (dict, list, or other JSON-serializable type)

**Example:**
```python
response = await client.proxy_salesforce_request(
    'conn-123',
    {
        'method': 'GET',
        'path': '/services/data/v59.0/query',
        'query': {'q': 'SELECT Id, Name FROM Account LIMIT 10'}
    }
)
```

##### `close()`

Close the aiohttp session. Call this when done with the client, or use the async context manager.

**Example:**
```python
await client.close()
```

## Error Handling

The SDK raises `AppnigmaAPIError` for all API errors. This exception includes:
- `status_code`: HTTP status code
- `error`: Error type/code
- `message`: Human-readable error message
- `response_body`: Full response body from API

**Example:**
```python
from appnigma_integrations_client import AppnigmaClient, AppnigmaAPIError

try:
    credentials = await client.get_connection_credentials('invalid-id')
except AppnigmaAPIError as e:
    print(f'API Error {e.status_code}: {e.message}')
    if e.status_code == 429:
        details = e.get_details()
        print(f'Rate limit exceeded. Plan limit: {details.get("planLimit")}')
except Exception as e:
    print(f'Unexpected error: {e}')
```

**Common Error Codes:**
- `400`: Bad Request - Missing required parameters or connection not in 'connected' status
- `401`: Unauthorized - Invalid or revoked API key
- `403`: Forbidden - API key doesn't match integration or connection doesn't belong to integration
- `404`: Not Found - Connection, Integration, or Company not found
- `429`: Too Many Requests - Monthly limit exceeded (includes `planLimit`, `currentUsage`, `offerings`)
- `500`: Internal Server Error - Server errors or token refresh failures

## Salesforce-Specific Examples

### SOQL Query

```python
response = await client.proxy_salesforce_request('conn-123', {
    'method': 'GET',
    'path': '/services/data/v59.0/query',
    'query': {
        'q': "SELECT Id, Name, Email FROM Contact WHERE AccountId = '001xx000003DGbQAAW' LIMIT 10"
    }
})

print(response['records'])
```

### Create Record (POST)

```python
new_contact = await client.proxy_salesforce_request('conn-123', {
    'method': 'POST',
    'path': '/services/data/v59.0/sobjects/Contact',
    'data': {
        'FirstName': 'John',
        'LastName': 'Doe',
        'Email': 'john.doe@example.com',
        'Phone': '555-1234'
    }
})

print(f"Created contact: {new_contact['id']}")
```

### Update Record (PATCH)

```python
await client.proxy_salesforce_request('conn-123', {
    'method': 'PATCH',
    'path': '/services/data/v59.0/sobjects/Contact/003xx000004DGbQAAW',
    'data': {
        'Email': 'newemail@example.com',
        'Phone': '555-5678'
    }
})
```

### Delete Record (DELETE)

```python
await client.proxy_salesforce_request('conn-123', {
    'method': 'DELETE',
    'path': '/services/data/v59.0/sobjects/Contact/003xx000004DGbQAAW'
})
```

## Configuration Options

### Base URL

The default base URL is `https://integrations.appnigma.ai`. You can override it for testing:

```python
client = AppnigmaClient(
    api_key='your-api-key',
    base_url='http://localhost:3000'  # For local development
)
```

### Debug Logging

Enable debug logging to see all HTTP requests and responses:

```python
import logging

client = AppnigmaClient(
    api_key='your-api-key',
    debug=True
)
```

Debug logs will show:
- HTTP method and URL
- Headers (with API key redacted)
- Request body
- Response status and body

**Note**: API keys are automatically redacted in debug logs for security.

## Type Hints

This SDK includes complete type hints for better IDE support and type checking:

```python
from appnigma_integrations_client import (
    AppnigmaClient,
    ConnectionCredentials,
    SalesforceProxyRequest,
    AppnigmaAPIError
)
```

## Requirements

- Python 3.8+
- aiohttp >= 3.8.0

## License

MIT

## Support

For issues, questions, or contributions, please visit our [GitHub repository](https://github.com/appnigma/appnigma-integrations-python).
