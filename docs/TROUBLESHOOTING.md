# Troubleshooting

Common issues and solutions when using the Appnigma Integrations Python SDK.

## Table of Contents

- [Authentication Issues](#authentication-issues)
- [Connection Issues](#connection-issues)
- [API Errors](#api-errors)
- [Performance Issues](#performance-issues)
- [Async/Await Issues](#asyncawait-issues)
- [Common Mistakes](#common-mistakes)

## Authentication Issues

### Error: "API key is required"

**Problem:** The SDK cannot find your API key.

**Solutions:**
1. Check that you've set the `APPNIGMA_API_KEY` environment variable:
   ```bash
   echo $APPNIGMA_API_KEY
   ```

2. Or provide it explicitly in the constructor:
   ```python
   client = AppnigmaClient(api_key='your-api-key-here')
   ```

3. Verify the API key is correct and hasn't been revoked in your dashboard.

### Error: 401 Unauthorized

**Problem:** The API key is invalid or has been revoked.

**Solutions:**
1. Verify your API key is correct:
   ```python
   import os
   api_key = os.getenv('APPNIGMA_API_KEY', '')
   print(f'API Key: {api_key[:10]}...' if api_key else 'API Key not set')
   ```

2. Check if the API key has been revoked in your dashboard.

3. Generate a new API key if needed.

4. Ensure you're using the correct API key for the correct integration.

### Error: 403 Forbidden

**Problem:** The API key doesn't have permission to access the requested resource.

**Solutions:**
1. Verify the connection belongs to the same integration as your API key.

2. Check that the integration is active and not deleted.

3. Ensure the connection is in 'connected' status.

## Connection Issues

### Error: 404 Not Found - Connection

**Problem:** The connection ID doesn't exist or doesn't belong to your integration.

**Solutions:**
1. Verify the connection ID is correct:
   ```python
   print(f'Connection ID: {connection_id}')
   ```

2. Check that the connection exists in your dashboard.

3. Ensure the connection belongs to the same integration as your API key.

4. Verify the connection is not revoked or deleted.

### Error: Connection not in 'connected' status

**Problem:** The connection exists but is not in a connected state.

**Solutions:**
1. Check the connection status in your dashboard.

2. Re-authenticate the connection if needed.

3. Test the connection using the test endpoint in your dashboard.

### Error: Token expired

**Problem:** The access token has expired and refresh failed.

**Solutions:**
1. The SDK should automatically refresh tokens, but if this fails:
   - Check that the refresh token is still valid
   - Verify the OAuth configuration is correct
   - Re-authenticate the connection if needed

2. Check the connection status in your dashboard.

## API Errors

### Error: 400 Bad Request

**Problem:** The request parameters are invalid.

**Common causes:**
1. **Invalid SOQL query:**
   ```python
   # ❌ Bad - Missing quotes around string
   query = {'q': "SELECT Id FROM Account WHERE Name = John"}
   
   # ✅ Good - Properly quoted
   query = {'q': "SELECT Id FROM Account WHERE Name = 'John'"}
   ```

2. **Invalid Salesforce API path:**
   ```python
   # ❌ Bad - Missing version
   path = '/services/data/query'
   
   # ✅ Good - Include API version
   path = '/services/data/v59.0/query'
   ```

3. **Invalid request body:**
   ```python
   # ❌ Bad - Missing required fields
   data = {'Email': 'test@example.com'}
   
   # ✅ Good - Include all required fields
   data = {'FirstName': 'John', 'LastName': 'Doe', 'Email': 'test@example.com'}
   ```

**Solutions:**
1. Validate your SOQL queries before sending:
   ```python
   def validate_soql(soql: str) -> bool:
       return 'SELECT' in soql.upper() and 'FROM' in soql.upper()
   ```

2. Check Salesforce API documentation for required fields.

3. Enable debug mode to see the exact request being sent:
   ```python
   client = AppnigmaClient(api_key=os.getenv('APPNIGMA_API_KEY'), debug=True)
   ```

### Error: 429 Too Many Requests

**Problem:** You've exceeded your rate limit.

**Solutions:**
1. **Check your usage:**
   ```python
   except AppnigmaAPIError as e:
       if e.status_code == 429:
           details = e.get_details()
           print(f"Plan Limit: {details.get('planLimit')}")
           print(f"Current Usage: {details.get('currentUsage')}")
   ```

2. **Implement exponential backoff:**
   ```python
   async def retry_with_backoff(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return await func()
           except AppnigmaAPIError as e:
               if e.status_code == 429:
                   delay = (2 ** attempt) * 1.0
                   await asyncio.sleep(delay)
                   continue
               raise
   ```

3. **Reduce request frequency:**
   - Batch multiple operations
   - Cache frequently accessed data
   - Implement request queuing

4. **Upgrade your plan** if you consistently hit limits.

### Error: 500 Internal Server Error

**Problem:** The server encountered an error processing your request.

**Solutions:**
1. **Retry the request** - This might be a transient error:
   ```python
   async def retry_on_server_error(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return await func()
           except AppnigmaAPIError as e:
               if e.status_code >= 500:
                   if attempt < max_retries - 1:
                       await asyncio.sleep(1.0 * (attempt + 1))
                       continue
               raise
   ```

2. **Check the error message** for more details:
   ```python
   except AppnigmaAPIError as e:
       print(f'Error details: {e.response_body}')
   ```

3. **Contact support** if the error persists.

## Performance Issues

### Slow Response Times

**Problem:** Requests are taking too long.

**Solutions:**
1. **Reuse client instances:**
   ```python
   # ✅ Good - Reuse client
   client = AppnigmaClient(api_key=os.getenv('APPNIGMA_API_KEY'))
   # Use client multiple times
   await client.close()
   
   # ❌ Bad - Create new client each time
   async def make_request():
       client = AppnigmaClient(api_key=os.getenv('APPNIGMA_API_KEY'))
       # ...
       await client.close()
   ```

2. **Batch operations:**
   ```python
   # ✅ Good - Batch requests
   results = await asyncio.gather(*[
       client.proxy_salesforce_request(...) for req in requests
   ])
   
   # ❌ Bad - Sequential requests
   for req in requests:
       await client.proxy_salesforce_request(...)
   ```

3. **Cache frequently accessed data:**
   ```python
   cache = {}
   
   async def get_cached_account(connection_id: str, account_id: str):
       key = f'{connection_id}:{account_id}'
       if key in cache:
           return cache[key]
       
       account = await client.proxy_salesforce_request(...)
       cache[key] = account
       return account
   ```

4. **Optimize SOQL queries:**
   - Only select fields you need
   - Use WHERE clauses to filter data
   - Use LIMIT to restrict result size

### Memory Issues

**Problem:** High memory usage when processing large datasets.

**Solutions:**
1. **Process data in chunks:**
   ```python
   async def process_large_dataset(connection_id: str):
       all_records = []
       next_records_url = None
       
       async with AppnigmaClient() as client:
           while True:
               path = next_records_url or '/services/data/v59.0/query'
               query = None if next_records_url else {'q': 'SELECT Id FROM Account'}
               
               response = await client.proxy_salesforce_request(connection_id, {
                   'method': 'GET',
                   'path': path,
                   'query': query
               })
               
               # Process records in batches
               for record in response['records']:
                   await process_record(record)
               
               next_records_url = response.get('nextRecordsUrl')
               if not next_records_url:
                   break
   ```

2. **Use generators for large responses** (if supported by your use case).

## Async/Await Issues

### Error: "coroutine was never awaited"

**Problem:** Forgot to await an async function.

**Solutions:**
1. **Always await async functions:**
   ```python
   # ❌ Bad - Missing await
   response = client.proxy_salesforce_request(connection_id, {...})
   
   # ✅ Good - Properly awaited
   response = await client.proxy_salesforce_request(connection_id, {...})
   ```

2. **Ensure your function is async:**
   ```python
   # ❌ Bad - Not async
   def query_accounts(connection_id: str):
       return client.proxy_salesforce_request(connection_id, {...})
   
   # ✅ Good - Async function
   async def query_accounts(connection_id: str):
       return await client.proxy_salesforce_request(connection_id, {...})
   ```

### Error: "RuntimeError: Event loop is closed"

**Problem:** Trying to use the client after the event loop is closed.

**Solutions:**
1. **Use async context manager:**
   ```python
   # ✅ Good - Context manager handles cleanup
   async with AppnigmaClient() as client:
       response = await client.proxy_salesforce_request(...)
   ```

2. **Ensure proper event loop management:**
   ```python
   # ✅ Good
   async def main():
       async with AppnigmaClient() as client:
           # Use client
           pass
   
   asyncio.run(main())
   ```

### Error: "aiohttp client session is closed"

**Problem:** Trying to use the client after it's been closed.

**Solutions:**
1. **Don't reuse closed clients:**
   ```python
   # ❌ Bad - Reusing closed client
   client = AppnigmaClient()
   await client.close()
   await client.proxy_salesforce_request(...)  # Error!
   
   # ✅ Good - Create new client
   async with AppnigmaClient() as client:
       await client.proxy_salesforce_request(...)
   ```

2. **Use context managers to ensure proper cleanup:**
   ```python
   async with AppnigmaClient() as client:
       # Client is automatically closed when exiting context
       pass
   ```

## Common Mistakes

### Mistake 1: Not Handling Errors

```python
# ❌ Bad - No error handling
response = await client.proxy_salesforce_request(connection_id, {...})

# ✅ Good - Proper error handling
try:
    response = await client.proxy_salesforce_request(connection_id, {...})
except AppnigmaAPIError as e:
    # Handle API errors
    pass
except Exception as e:
    # Handle other errors
    pass
```

### Mistake 2: Creating New Client for Each Request

```python
# ❌ Bad - Creates new client each time
async def query(connection_id: str):
    client = AppnigmaClient(api_key=os.getenv('APPNIGMA_API_KEY'))
    try:
        return await client.proxy_salesforce_request(connection_id, {...})
    finally:
        await client.close()

# ✅ Good - Reuse client
client = AppnigmaClient(api_key=os.getenv('APPNIGMA_API_KEY'))

async def query(connection_id: str):
    return await client.proxy_salesforce_request(connection_id, {...})
```

### Mistake 3: Not Checking Response Structure

```python
# ❌ Bad - Assumes response structure
records = response['records']  # Might raise KeyError

# ✅ Good - Check response structure
if 'records' in response and isinstance(response['records'], list):
    for record in response['records']:
        # Process record
        pass
```

### Mistake 4: Hardcoding API Versions

```python
# ❌ Bad - Hardcoded version
path = '/services/data/v59.0/query'

# ✅ Good - Make version configurable
API_VERSION = os.getenv('SALESFORCE_API_VERSION', 'v59.0')
path = f'/services/data/{API_VERSION}/query'
```

### Mistake 5: Not Validating Input

```python
# ❌ Bad - No validation
async def get_account(connection_id: str, account_id: str):
    return await client.proxy_salesforce_request(connection_id, {
        'method': 'GET',
        'path': f'/services/data/v59.0/sobjects/Account/{account_id}'
    })

# ✅ Good - Validate input
async def get_account(connection_id: str, account_id: str):
    if not connection_id or not account_id:
        raise ValueError('Connection ID and Account ID are required')
    
    if not re.match(r'^[a-zA-Z0-9]{15,18}$', account_id):
        raise ValueError('Invalid Account ID format')
    
    return await client.proxy_salesforce_request(connection_id, {
        'method': 'GET',
        'path': f'/services/data/v59.0/sobjects/Account/{account_id}'
    })
```

### Mistake 6: Not Using Context Managers

```python
# ❌ Bad - Manual cleanup
client = AppnigmaClient()
try:
    response = await client.proxy_salesforce_request(...)
finally:
    await client.close()

# ✅ Good - Context manager
async with AppnigmaClient() as client:
    response = await client.proxy_salesforce_request(...)
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs:** Enable debug mode to see detailed request/response information
2. **Review the API Reference:** Ensure you're using the SDK correctly
3. **Check the Examples:** Look for similar use cases in the examples
4. **Contact Support:** Reach out to support@appnigma.ai with:
   - Error messages
   - Code snippets (with sensitive data redacted)
   - Steps to reproduce
   - SDK version
   - Python version

## Debug Checklist

When troubleshooting, check:

- [ ] API key is set and valid
- [ ] Connection ID exists and is in 'connected' status
- [ ] Integration ID matches your API key (if provided)
- [ ] Request parameters are valid (SOQL syntax, API paths, etc.)
- [ ] Network connectivity is working
- [ ] Rate limits haven't been exceeded
- [ ] SDK version is up to date
- [ ] Python version is compatible (3.8+)
- [ ] Debug mode is enabled to see request/response details
- [ ] All async functions are properly awaited
- [ ] Client is properly closed or using context manager
