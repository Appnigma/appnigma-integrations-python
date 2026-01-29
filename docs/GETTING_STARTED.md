# Getting Started with Appnigma Integrations Python SDK

Welcome to the Appnigma Integrations Python SDK! This guide will help you get up and running quickly.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Basic Usage](#basic-usage)
- [Next Steps](#next-steps)

## Installation

Install the SDK using pip:

```bash
pip install appnigma-integrations-client
```

### Requirements

- Python 3.8 or higher
- aiohttp >= 3.8.0
- typing_extensions >= 4.0.0 (for Python < 3.11)

## Quick Start

Here's a minimal example to get you started:

```python
import asyncio
from appnigma_integrations_client import AppnigmaClient

async def main():
    # Initialize the client
    client = AppnigmaClient(api_key='your-api-key-here')
    
    # Get connection credentials
    credentials = await client.get_connection_credentials('connection-id')
    
    print('Access Token:', credentials['accessToken'])
    print('Instance URL:', credentials['instanceUrl'])
    
    # Clean up
    await client.close()

asyncio.run(main())
```

### Using Async Context Manager

The SDK supports async context managers for automatic resource cleanup:

```python
import asyncio
from appnigma_integrations_client import AppnigmaClient

async def main():
    async with AppnigmaClient(api_key='your-api-key-here') as client:
        credentials = await client.get_connection_credentials('connection-id')
        print('Access Token:', credentials['accessToken'])

asyncio.run(main())
```

## Authentication

The SDK requires an API key for authentication. API keys are integration-scoped, meaning each key is tied to a specific integration.

### Getting Your API Key

1. Log in to your Appnigma dashboard
2. Navigate to your integration settings
3. Generate a new API key
4. **Important**: Copy the key immediately - it's only shown once!

### Setting Your API Key

You can provide your API key in two ways:

#### Option 1: Environment Variable (Recommended)

Set the `APPNIGMA_API_KEY` environment variable:

```bash
export APPNIGMA_API_KEY=your-api-key-here
```

Then initialize the client without providing the key:

```python
client = AppnigmaClient()
```

#### Option 2: Constructor Parameter

Pass the API key directly when creating the client:

```python
client = AppnigmaClient(api_key='your-api-key-here')
```

**Security Note**: Never commit API keys to version control. Always use environment variables in production.

## Basic Usage

### Listing Connections

List connections for the integration (integration is derived from your API key):

```python
result = await client.list_connections()
print(f'Found {result["totalCount"]} connections')
for conn in result['connections']:
    print(conn['connectionId'], conn['userEmail'], conn['status'])
```

Optional parameters: `environment`, `status`, `search`, `limit`, `cursor` (pagination).

### Getting Connection Credentials

Retrieve access tokens and metadata for a Salesforce connection:

```python
credentials = await client.get_connection_credentials('connection-id')

# Credentials include:
# - accessToken: The Salesforce access token
# - instanceUrl: The Salesforce instance URL
# - environment: Production or sandbox
# - region: Geographic region
# - tokenType: Usually "Bearer"
# - expiresAt: ISO 8601 expiration timestamp

print('Access Token:', credentials['accessToken'])
print('Instance URL:', credentials['instanceUrl'])
print('Environment:', credentials['environment'])
print('Expires At:', credentials['expiresAt'])
```

### Making Salesforce API Calls

Use the proxy method to make API calls to Salesforce:

```python
# Query Salesforce data
response = await client.proxy_salesforce_request('connection-id', {
    'method': 'GET',
    'path': '/services/data/v59.0/query',
    'query': {
        'q': 'SELECT Id, Name FROM Account LIMIT 10'
    }
})

print('Records:', response['records'])
```

The SDK automatically handles:
- Token refresh when tokens expire
- Usage tracking for billing
- Error handling and retries

### Integration ID

The `integration_id` parameter is optional. If your API key is integration-scoped (which it is by default), the SDK automatically extracts the integration ID from your API key. You only need to provide it explicitly if you're using a company-level API key.

```python
# Integration ID is automatically extracted from API key
credentials = await client.get_connection_credentials('connection-id')

# Or explicitly provide it (rarely needed)
credentials = await client.get_connection_credentials(
    'connection-id',
    integration_id='integration-id'
)
```

## Configuration Options

### Base URL

By default, the SDK connects to `https://integrations.appnigma.ai`. For local development or testing, you can override this:

```python
client = AppnigmaClient(
    api_key='your-api-key',
    base_url='http://localhost:3000'
)
```

### Debug Mode

Enable debug logging to see all HTTP requests and responses:

```python
import logging

client = AppnigmaClient(
    api_key='your-api-key',
    debug=True
)
```

Debug logs include:
- HTTP method and URL
- Request headers (API key is automatically redacted)
- Request body
- Response status and body

**Note**: Debug mode should only be enabled during development, not in production.

## Error Handling

The SDK raises `AppnigmaAPIError` for all API errors:

```python
from appnigma_integrations_client import AppnigmaClient, AppnigmaAPIError

try:
    credentials = await client.get_connection_credentials('invalid-id')
except AppnigmaAPIError as e:
    print(f'API Error {e.status_code}: {e.message}')
    
    # Handle rate limiting
    if e.status_code == 429:
        details = e.get_details()
        print(f'Rate limit exceeded. Plan limit: {details.get("planLimit")}')
except Exception as e:
    print(f'Unexpected error: {e}')
```

Common error codes:
- `400`: Bad Request - Invalid parameters
- `401`: Unauthorized - Invalid or revoked API key
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource doesn't exist
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server error

## Async/Await Pattern

The SDK is fully async and uses Python's `asyncio` library. All methods are coroutines and must be awaited:

```python
import asyncio
from appnigma_integrations_client import AppnigmaClient

async def main():
    async with AppnigmaClient(api_key='your-api-key') as client:
        # All SDK methods are async
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

Always close the client when done, or use the async context manager:

```python
# Option 1: Explicit close
client = AppnigmaClient(api_key='your-api-key')
try:
    # Use client
    await client.get_connection_credentials('connection-id')
finally:
    await client.close()

# Option 2: Async context manager (recommended)
async with AppnigmaClient(api_key='your-api-key') as client:
    # Use client
    await client.get_connection_credentials('connection-id')
# Client is automatically closed
```

## Next Steps

- Read the [API Reference](./API_REFERENCE.md) for detailed method documentation
- Check out [Examples](./EXAMPLES.md) for common use cases
- Review [Best Practices](./BEST_PRACTICES.md) for production-ready code
- See [Troubleshooting](./TROUBLESHOOTING.md) if you encounter issues

## Type Hints

The SDK includes complete type hints for better IDE support:

```python
from appnigma_integrations_client import (
    AppnigmaClient,
    ConnectionCredentials,
    SalesforceProxyRequest,
    AppnigmaAPIError
)

async def get_credentials(
    client: AppnigmaClient,
    connection_id: str
) -> ConnectionCredentials:
    return await client.get_connection_credentials(connection_id)
```

## Support

- **Documentation**: See the other guides in this `docs` folder
- **Issues**: Report bugs or request features on [GitHub](https://github.com/appnigma/appnigma-integrations-python)
- **Questions**: Contact support at support@appnigma.ai
