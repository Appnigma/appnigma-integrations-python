# Examples

Practical examples demonstrating common use cases with the Appnigma Integrations Python SDK.

## Table of Contents

- [Basic Operations](#basic-operations)
- [Salesforce API Operations](#salesforce-api-operations)
- [Error Handling](#error-handling)
- [Advanced Patterns](#advanced-patterns)
- [Real-World Scenarios](#real-world-scenarios)

## Basic Operations

### Initialize Client

```python
import asyncio
from appnigma_integrations_client import AppnigmaClient

# Using environment variable
async def main():
    client = AppnigmaClient()
    # Use client
    await client.close()

# Or with explicit configuration
async def main():
    client = AppnigmaClient(
        api_key=os.getenv('APPNIGMA_API_KEY'),
        base_url='https://integrations.appnigma.ai',
        debug=False
    )
    # Use client
    await client.close()

# Or with async context manager (recommended)
async def main():
    async with AppnigmaClient(api_key='your-api-key') as client:
        # Use client
        pass
```

### Get Connection Credentials

```python
async def get_credentials(connection_id: str):
    async with AppnigmaClient() as client:
        credentials = await client.get_connection_credentials(connection_id)
        
        print('Access Token:', credentials['accessToken'])
        print('Instance URL:', credentials['instanceUrl'])
        print('Environment:', credentials['environment'])
        print('Region:', credentials['region'])
        print('Expires At:', credentials['expiresAt'])
        
        return credentials
```

## Salesforce API Operations

### SOQL Queries

#### Simple Query

```python
async def query_accounts(connection_id: str):
    async with AppnigmaClient() as client:
        response = await client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {
                'q': 'SELECT Id, Name, Type FROM Account LIMIT 10'
            }
        })
        
        print(f"Found {response['totalSize']} accounts")
        for account in response['records']:
            print(f"{account['Name']} ({account.get('Type', 'N/A')})")
        
        return response['records']
```

#### Query with Filters

```python
async def query_contacts_by_account(connection_id: str, account_id: str):
    soql = f"SELECT Id, Name, Email, Phone FROM Contact WHERE AccountId = '{account_id}' ORDER BY Name LIMIT 100"
    
    async with AppnigmaClient() as client:
        response = await client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {'q': soql}
        })
        
        return response['records']
```

#### Paginated Query

```python
async def query_all_accounts(connection_id: str):
    all_records = []
    next_records_url = None
    
    async with AppnigmaClient() as client:
        while True:
            path = next_records_url.replace('https://', '').split('/', 1)[1] if next_records_url else '/services/data/v59.0/query'
            query = None if next_records_url else {'q': 'SELECT Id, Name FROM Account'}
            
            response = await client.proxy_salesforce_request(connection_id, {
                'method': 'GET',
                'path': path,
                'query': query
            })
            
            all_records.extend(response['records'])
            next_records_url = response.get('nextRecordsUrl')
            
            if not next_records_url:
                break
    
    return all_records
```

### Create Records

```python
async def create_contact(connection_id: str, contact_data: dict):
    async with AppnigmaClient() as client:
        response = await client.proxy_salesforce_request(connection_id, {
            'method': 'POST',
            'path': '/services/data/v59.0/sobjects/Contact',
            'data': contact_data
        })
        
        print(f"Created contact with ID: {response['id']}")
        return response
```

### Update Records

```python
async def update_contact(connection_id: str, contact_id: str, updates: dict):
    async with AppnigmaClient() as client:
        response = await client.proxy_salesforce_request(connection_id, {
            'method': 'PATCH',
            'path': f'/services/data/v59.0/sobjects/Contact/{contact_id}',
            'data': updates
        })
        
        print(f"Updated contact {contact_id}")
        return response
```

### Delete Records

```python
async def delete_contact(connection_id: str, contact_id: str):
    async with AppnigmaClient() as client:
        await client.proxy_salesforce_request(connection_id, {
            'method': 'DELETE',
            'path': f'/services/data/v59.0/sobjects/Contact/{contact_id}'
        })
        
        print(f"Deleted contact {contact_id}")
```

### Bulk Operations

```python
async def bulk_create_contacts(connection_id: str, contacts: list):
    async with AppnigmaClient() as client:
        results = await asyncio.gather(
            *[
                client.proxy_salesforce_request(connection_id, {
                    'method': 'POST',
                    'path': '/services/data/v59.0/sobjects/Contact',
                    'data': contact
                })
                for contact in contacts
            ],
            return_exceptions=True
        )
        
        successful = [r for r in results if not isinstance(r, Exception)]
        failed = [r for r in results if isinstance(r, Exception)]
        
        print(f"Created {len(successful)} contacts")
        if failed:
            print(f"Failed to create {len(failed)} contacts")
        
        return {'successful': successful, 'failed': failed}
```

### Describe Objects

```python
async def describe_object(connection_id: str, object_type: str):
    async with AppnigmaClient() as client:
        response = await client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': f'/services/data/v59.0/sobjects/{object_type}/describe'
        })
        
        print(f"Object: {response['name']}")
        print(f"Fields: {len(response['fields'])}")
        
        return response
```

## Error Handling

### Basic Error Handling

```python
from appnigma_integrations_client import AppnigmaAPIError

async def safe_query(connection_id: str):
    async with AppnigmaClient() as client:
        try:
            response = await client.proxy_salesforce_request(connection_id, {
                'method': 'GET',
                'path': '/services/data/v59.0/query',
                'query': {'q': 'SELECT Id FROM Account LIMIT 10'}
            })
            
            return response
        except AppnigmaAPIError as e:
            print(f'API Error {e.status_code}: {e.message}')
            
            if e.status_code == 400:
                print('Bad request - check your query syntax')
            elif e.status_code == 401:
                print('Unauthorized - check your API key')
            elif e.status_code == 404:
                print('Connection not found')
            elif e.status_code == 429:
                details = e.get_details()
                print(f"Rate limit exceeded. Limit: {details.get('planLimit')}, "
                      f"Usage: {details.get('currentUsage')}")
            else:
                print('Unexpected API error')
            
            raise
        except Exception as e:
            print(f'Unexpected error: {e}')
            raise
```

### Retry Logic with Exponential Backoff

```python
import asyncio
from appnigma_integrations_client import AppnigmaAPIError

async def retry_request(func, max_retries: int = 3, base_delay: float = 1.0):
    for attempt in range(max_retries):
        try:
            return await func()
        except AppnigmaAPIError as e:
            # Don't retry client errors (4xx)
            if 400 <= e.status_code < 500 and e.status_code != 429:
                raise
            
            # For rate limits, wait longer
            if e.status_code == 429:
                delay = base_delay * (2 ** attempt) * 2
                print(f"Rate limited. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                continue
            
            # Last attempt or non-retryable error
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff
            delay = base_delay * (2 ** attempt)
            print(f"Request failed. Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(delay)
        except Exception as e:
            raise
    
    raise Exception('Max retries exceeded')

# Usage
async def query_with_retry(connection_id: str):
    async with AppnigmaClient() as client:
        return await retry_request(
            lambda: client.proxy_salesforce_request(connection_id, {
                'method': 'GET',
                'path': '/services/data/v59.0/query',
                'query': {'q': 'SELECT Id FROM Account LIMIT 10'}
            })
        )
```

## Advanced Patterns

### Type-Safe Queries

```python
from typing import TypedDict, List

class Account(TypedDict):
    Id: str
    Name: str
    Type: str
    Industry: str

class QueryResponse(TypedDict):
    totalSize: int
    done: bool
    records: List[Account]

async def get_accounts(connection_id: str) -> List[Account]:
    async with AppnigmaClient() as client:
        response: QueryResponse = await client.proxy_salesforce_request(
            connection_id,
            {
                'method': 'GET',
                'path': '/services/data/v59.0/query',
                'query': {
                    'q': 'SELECT Id, Name, Type, Industry FROM Account LIMIT 100'
                }
            }
        )
        
        return response['records']
```

### Connection Pooling

```python
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self._clients: Dict[str, AppnigmaClient] = {}
    
    def get_client(self, api_key: str) -> AppnigmaClient:
        if api_key not in self._clients:
            self._clients[api_key] = AppnigmaClient(api_key=api_key)
        return self._clients[api_key]
    
    async def query(self, api_key: str, connection_id: str, soql: str):
        client = self.get_client(api_key)
        return await client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {'q': soql}
        })
    
    async def close_all(self):
        for client in self._clients.values():
            await client.close()

# Usage
async def main():
    manager = ConnectionManager()
    try:
        await manager.query('api-key-1', 'conn-1', 'SELECT Id FROM Account')
        await manager.query('api-key-1', 'conn-2', 'SELECT Id FROM Contact')
    finally:
        await manager.close_all()
```

### Batch Operations

```python
async def batch_update_contacts(connection_id: str, updates: list):
    batch_size = 10
    results = []
    
    async with AppnigmaClient() as client:
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
            
            # Rate limit protection - small delay between batches
            if i + batch_size < len(updates):
                await asyncio.sleep(0.1)
    
    return results
```

## Real-World Scenarios

### Sync Contacts from Salesforce

```python
from datetime import datetime

async def sync_contacts(connection_id: str, last_sync_time: datetime = None):
    where_clause = f"WHERE LastModifiedDate >= {last_sync_time.isoformat()}" if last_sync_time else ""
    
    soql = f"""SELECT Id, FirstName, LastName, Email, Phone, LastModifiedDate
               FROM Contact
               {where_clause}
               ORDER BY LastModifiedDate
               LIMIT 2000"""
    
    async with AppnigmaClient() as client:
        response = await client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {'q': soql}
        })
        
        # Process contacts
        for contact in response['records']:
            # Save to your database, send webhooks, etc.
            print(f"Syncing contact: {contact.get('FirstName')} {contact.get('LastName')}")
        
        return {
            'synced': len(response['records']),
            'total': response['totalSize'],
            'next_sync_time': datetime.now()
        }
```

### Generate Report

```python
async def generate_account_report(connection_id: str):
    async with AppnigmaClient() as client:
        # Get account statistics
        accounts = await client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {
                'q': 'SELECT Type, COUNT(Id) total FROM Account GROUP BY Type'
            }
        })
        
        # Get contact statistics
        contacts = await client.proxy_salesforce_request(connection_id, {
            'method': 'GET',
            'path': '/services/data/v59.0/query',
            'query': {
                'q': 'SELECT COUNT(Id) total FROM Contact'
            }
        })
        
        return {
            'accounts_by_type': accounts['records'],
            'total_contacts': contacts['totalSize'],
            'generated_at': datetime.now().isoformat()
        }
```

### Webhook Integration

```python
from fastapi import FastAPI, HTTPException
from appnigma_integrations_client import AppnigmaClient

app = FastAPI()

@app.post('/webhook/salesforce')
async def handle_webhook(request: dict):
    connection_id = request.get('connection_id')
    event = request.get('event')
    data = request.get('data')
    
    try:
        async with AppnigmaClient() as client:
            if event == 'contact.created':
                await handle_new_contact(client, connection_id, data)
            elif event == 'account.updated':
                await handle_account_update(client, connection_id, data)
        
        return {'success': True}
    except Exception as e:
        print(f'Webhook error: {e}')
        raise HTTPException(status_code=500, detail='Internal server error')

async def handle_new_contact(client: AppnigmaClient, connection_id: str, contact_id: str):
    contact = await client.proxy_salesforce_request(connection_id, {
        'method': 'GET',
        'path': f'/services/data/v59.0/sobjects/Contact/{contact_id}'
    })
    
    # Process contact (save to database, send notifications, etc.)
    print(f'New contact: {contact}')
```

### Scheduled Sync Job

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Sync every hour
async def scheduled_sync():
    print('Starting scheduled sync...')
    
    try:
        connection_id = os.getenv('SALESFORCE_CONNECTION_ID')
        last_sync_time = await get_last_sync_time()  # From your database
        
        result = await sync_contacts(connection_id, last_sync_time)
        
        await save_last_sync_time(datetime.now())  # Save to your database
        
        print(f"Sync completed: {result['synced']} contacts synced")
    except Exception as e:
        print(f'Sync failed: {e}')
        # Send alert, log to monitoring service, etc.

# Schedule the job
scheduler = AsyncIOScheduler()
scheduler.add_job(scheduled_sync, 'cron', hour='*')  # Every hour
scheduler.start()

# Keep the script running
try:
    asyncio.get_event_loop().run_forever()
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
```
