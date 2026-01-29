# Best Practices

Guidelines and recommendations for using the Appnigma Integrations Python SDK effectively in production.

## Table of Contents

- [Security](#security)
- [Performance](#performance)
- [Error Handling](#error-handling)
- [Code Organization](#code-organization)
- [Monitoring & Logging](#monitoring--logging)
- [Rate Limiting](#rate-limiting)

## Security

### API Key Management

**✅ DO:**
- Store API keys in environment variables
- Use secrets management services (AWS Secrets Manager, HashiCorp Vault, etc.)
- Rotate API keys regularly
- Use different API keys for different environments (dev, staging, production)

**❌ DON'T:**
- Commit API keys to version control
- Hardcode API keys in source code
- Share API keys in chat or email
- Use the same API key across multiple applications

```python
# ✅ Good
client = AppnigmaClient(api_key=os.getenv('APPNIGMA_API_KEY'))

# ❌ Bad
client = AppnigmaClient(api_key='hardcoded-key-here')
```

### Environment Variables

Use a `.env` file for local development (and add it to `.gitignore`):

```bash
# .env
APPNIGMA_API_KEY=your-api-key-here
APPNIGMA_BASE_URL=https://integrations.appnigma.ai
```

```python
import os
from dotenv import load_dotenv

load_dotenv()

client = AppnigmaClient(
    api_key=os.getenv('APPNIGMA_API_KEY'),
    base_url=os.getenv('APPNIGMA_BASE_URL')
)
```

### Debug Mode

**Never enable debug mode in production** - it logs sensitive information:

```python
# ✅ Good
client = AppnigmaClient(
    api_key=os.getenv('APPNIGMA_API_KEY'),
    debug=os.getenv('DEBUG', 'False').lower() == 'true'
)

# ❌ Bad
client = AppnigmaClient(
    api_key=os.getenv('APPNIGMA_API_KEY'),
    debug=True  # Always enabled
)
```

## Performance

### Connection Reuse

Reuse client instances instead of creating new ones for each request:

```python
# ✅ Good - Reuse client
class SalesforceService:
    def __init__(self):
        self.client = AppnigmaClient(api_key=os.getenv('APPNIGMA_API_KEY'))
    
    async def query(self, connection_id: str, soql: str):
        return await self.client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {'q': soql}
        })
    
    async def close(self):
        await self.client.close()

# ❌ Bad - Create new client for each request
async def query(connection_id: str, soql: str):
    client = AppnigmaClient(api_key=os.getenv('APPNIGMA_API_KEY'))
    try:
        return await client.proxy_salesforce_request(connection_id, { /* ... */ })
    finally:
        await client.close()
```

### Async Context Manager

Use async context managers for automatic resource cleanup:

```python
# ✅ Good - Context manager
async def query(connection_id: str, soql: str):
    async with AppnigmaClient(api_key=os.getenv('APPNIGMA_API_KEY')) as client:
        return await client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {'q': soql}
        })
```

### Batch Operations

When making multiple requests, batch them to reduce overhead:

```python
# ✅ Good - Batch requests
async def update_multiple_contacts(connection_id: str, updates: list):
    async with AppnigmaClient() as client:
        batch_size = 10
        results = []
        
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[
                    client.proxy_salesforce_request(connection_id, {
                        'method': 'PATCH',
                        'path': f'/services/data/v59.0/sobjects/Contact/{update["id"]}',
                        'data': update['data']
                    })
                    for update in batch
                ],
                return_exceptions=True
            )
            results.extend(batch_results)
        
        return results

# ❌ Bad - Sequential requests
async def update_multiple_contacts(connection_id: str, updates: list):
    async with AppnigmaClient() as client:
        results = []
        for update in updates:
            result = await client.proxy_salesforce_request(connection_id, { /* ... */ })
            results.append(result)
        return results
```

### Caching

Cache frequently accessed data to reduce API calls:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedSalesforceService:
    def __init__(self):
        self.client = AppnigmaClient(api_key=os.getenv('APPNIGMA_API_KEY'))
        self._cache = {}
        self._cache_ttl = {}
    
    async def get_account(self, connection_id: str, account_id: str):
        cache_key = f'account:{connection_id}:{account_id}'
        
        # Check cache first
        if cache_key in self._cache:
            if self._cache_ttl[cache_key] > datetime.now():
                return self._cache[cache_key]
        
        # Fetch from API
        account = await self.client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': f'/services/data/v59.0/sobjects/Account/{account_id}'
        })
        
        # Store in cache (1 hour TTL)
        self._cache[cache_key] = account
        self._cache_ttl[cache_key] = datetime.now() + timedelta(hours=1)
        
        return account
```

## Error Handling

### Comprehensive Error Handling

Always handle errors appropriately:

```python
import logging
from appnigma_integrations_client import AppnigmaAPIError

logger = logging.getLogger(__name__)

async def safe_operation(connection_id: str):
    async with AppnigmaClient() as client:
        try:
            return await client.proxy_salesforce_request(connection_id, { /* ... */ })
        except AppnigmaAPIError as e:
            # Handle API errors
            if e.status_code == 400:
                logger.error('Invalid request', extra={'error': e.message})
                raise ValueError('Invalid request. Please check your parameters.')
            elif e.status_code == 401:
                logger.error('Authentication failed', extra={'error': e.message})
                raise ValueError('Authentication failed. Please check your API key.')
            elif e.status_code == 404:
                logger.warning('Resource not found', extra={'error': e.message})
                raise ValueError('Resource not found.')
            elif e.status_code == 429:
                details = e.get_details()
                logger.warning('Rate limit exceeded', extra=details)
                raise ValueError(f"Rate limit exceeded. Limit: {details.get('planLimit')}, "
                               f"Usage: {details.get('currentUsage')}")
            elif e.status_code >= 500:
                logger.error('Server error', extra={'status_code': e.status_code})
                raise RuntimeError('Service temporarily unavailable. Please try again later.')
            else:
                logger.error('Unexpected API error', extra={
                    'status_code': e.status_code,
                    'error': e.message
                })
                raise RuntimeError('An unexpected error occurred.')
        except Exception as e:
            logger.error('Unexpected error', exc_info=True)
            raise
```

### Retry Logic

Implement retry logic for transient failures:

```python
import asyncio
from appnigma_integrations_client import AppnigmaAPIError

async def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    for attempt in range(max_retries):
        try:
            return await func()
        except AppnigmaAPIError as e:
            # Don't retry client errors (except 429)
            if 400 <= e.status_code < 500 and e.status_code != 429:
                raise
            
            # Last attempt
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
        except Exception as e:
            raise
    
    raise Exception('Max retries exceeded')
```

## Code Organization

### Service Layer Pattern

Organize your code into service layers:

```python
# services/salesforce_service.py
from appnigma_integrations_client import AppnigmaClient

class SalesforceService:
    def __init__(self, api_key: str):
        self.client = AppnigmaClient(api_key=api_key)
    
    async def get_account(self, connection_id: str, account_id: str):
        return await self.client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': f'/services/data/v59.0/sobjects/Account/{account_id}'
        })
    
    async def query_accounts(self, connection_id: str, filters: dict = None):
        soql = self._build_soql('Account', ['Id', 'Name', 'Type'], filters)
        return await self.client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {'q': soql}
        })
    
    def _build_soql(self, object_type: str, fields: list, filters: dict = None) -> str:
        # Build SOQL query logic
        query = f"SELECT {', '.join(fields)} FROM {object_type}"
        if filters:
            # Add WHERE clause logic
            pass
        return query
    
    async def close(self):
        await self.client.close()
```

### Type Safety

Use type hints for better code safety:

```python
from typing import TypedDict, List, Optional

class Account(TypedDict):
    Id: str
    Name: str
    Type: Optional[str]
    Industry: Optional[str]

class QueryResponse(TypedDict):
    totalSize: int
    done: bool
    records: List[Account]

class TypedSalesforceService:
    def __init__(self, api_key: str):
        self.client = AppnigmaClient(api_key=api_key)
    
    async def get_account(self, connection_id: str, account_id: str) -> Account:
        return await self.client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': f'/services/data/v59.0/sobjects/Account/{account_id}'
        })
    
    async def query_accounts(self, connection_id: str) -> QueryResponse:
        return await self.client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {'q': 'SELECT Id, Name, Type FROM Account LIMIT 100'}
        })
```

## Monitoring & Logging

### Structured Logging

Use structured logging for better observability:

```python
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

async def query_with_logging(connection_id: str, soql: str):
    start_time = time.time()
    
    try:
        logger.info('Salesforce query started', extra={
            'connection_id': connection_id,
            'soql': soql,
            'timestamp': datetime.now().isoformat()
        })
        
        async with AppnigmaClient() as client:
            response = await client.proxy_salesforce_request(connection_id, {
                'method': 'GET',
                'path': '/services/data/v59.0/query',
                'query': {'q': soql}
            })
        
        duration = time.time() - start_time
        logger.info('Salesforce query completed', extra={
            'connection_id': connection_id,
            'duration': duration,
            'record_count': len(response.get('records', []))
        })
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error('Salesforce query failed', extra={
            'connection_id': connection_id,
            'soql': soql,
            'duration': duration,
            'error': str(e)
        }, exc_info=True)
        raise
```

### Metrics Collection

Track metrics for monitoring:

```python
from collections import defaultdict

class MetricsCollector:
    def __init__(self):
        self.metrics = defaultdict(int)
    
    def increment(self, metric: str, value: int = 1):
        self.metrics[metric] += value
    
    def get_metrics(self) -> dict:
        return dict(self.metrics)

metrics = MetricsCollector()

async def query_with_metrics(connection_id: str, soql: str):
    start_time = time.time()
    
    try:
        metrics.increment('salesforce.requests.total')
        async with AppnigmaClient() as client:
            response = await client.proxy_salesforce_request(connection_id, { /* ... */ })
        
        duration = time.time() - start_time
        metrics.increment('salesforce.requests.success')
        metrics.increment('salesforce.requests.duration', int(duration * 1000))
        
        return response
    except Exception as e:
        metrics.increment('salesforce.requests.errors')
        raise
```

## Rate Limiting

### Handle Rate Limits Gracefully

```python
async def handle_rate_limit(func, max_retries: int = 5):
    for attempt in range(max_retries):
        try:
            return await func()
        except AppnigmaAPIError as e:
            if e.status_code == 429:
                details = e.get_details()
                retry_after = 60  # Default 60 seconds
                
                if details.get('planLimit') and details.get('currentUsage'):
                    # Estimate retry time based on usage
                    retry_after = max(60, int(
                        (details['planLimit'] - details['currentUsage']) / 100 * 60
                    ))
                
                if attempt < max_retries - 1:
                    logger.warning('Rate limit exceeded, retrying', extra={
                        'attempt': attempt + 1,
                        'retry_after': retry_after,
                        'details': details
                    })
                    
                    await asyncio.sleep(retry_after)
                    continue
            
            raise
    
    raise Exception('Max retries exceeded')
```

### Rate Limit Monitoring

Monitor your rate limit usage:

```python
from datetime import datetime, timedelta

class RateLimitMonitor:
    def __init__(self):
        self.usage = {}
    
    async def check_rate_limit(self, connection_id: str) -> bool:
        key = f'rate_limit:{connection_id}'
        current = self.usage.get(key)
        
        if current and current['reset_at'] > datetime.now():
            return current['count'] < 100  # Assuming 100 requests per minute
        
        # Reset counter
        self.usage[key] = {
            'count': 0,
            'reset_at': datetime.now() + timedelta(minutes=1)
        }
        
        return True
    
    def increment(self, connection_id: str):
        key = f'rate_limit:{connection_id}'
        if key in self.usage:
            self.usage[key]['count'] += 1
```

## Additional Tips

1. **Use async context managers**: Always use `async with` for automatic resource cleanup
2. **Implement circuit breakers**: Stop making requests if the service is down
3. **Set timeouts**: Configure appropriate timeouts for your use case
4. **Monitor API usage**: Track your usage to avoid hitting limits
5. **Test error scenarios**: Write tests for error handling paths
6. **Document your integration**: Keep documentation up to date
7. **Version your API calls**: Use specific Salesforce API versions in paths
8. **Use type hints**: Improve code quality and IDE support
9. **Handle async properly**: Ensure all async operations are properly awaited
10. **Clean up resources**: Always close clients or use context managers
