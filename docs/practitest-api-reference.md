# PractiTest API Reference

## PractiTestClient Class

The `PractiTestClient` class provides a Python interface to the PractiTest v2 API.

### Constructor

```python
PractiTestClient(email: str, token: str, project_id: str)
```

Creates a new PractiTest client instance.

**Parameters:**
- `email` (str): PractiTest account email
- `token` (str): PractiTest API token
- `project_id` (str): Target project ID

**Example:**
```python
from utils.practitest_client import PractiTestClient

client = PractiTestClient(
    email="user@company.com",
    token="your-api-token",
    project_id="12345"
)
```

### Methods

#### `create_test_set(name: str, description: str = None) -> Optional[str]`

Creates a new test set in PractiTest.

**Parameters:**
- `name` (str): Test set name
- `description` (str, optional): Test set description

**Returns:**
- `str`: Test set ID if successful
- `None`: If creation failed

**Example:**
```python
test_set_id = client.create_test_set(
    name="Automated Test Run",
    description="Pytest automation run"
)
```

#### `get_test_by_display_id(display_id: str) -> Optional[Dict[str, Any]]`

Retrieves test information by display ID.

**Parameters:**
- `display_id` (str): PractiTest test display ID

**Returns:**
- `dict`: Test data if found
- `None`: If test not found

**Example:**
```python
test_data = client.get_test_by_display_id("697")
if test_data:
    print(f"Test ID: {test_data['id']}")
    print(f"Test Name: {test_data['attributes']['name']}")
```

#### `create_test_instance(test_id: str, test_set_id: str) -> Optional[str]`

Creates a test instance within a test set.

**Parameters:**
- `test_id` (str): PractiTest test ID
- `test_set_id` (str): Target test set ID

**Returns:**
- `str`: Instance ID if successful
- `None`: If creation failed

**Example:**
```python
instance_id = client.create_test_instance(
    test_id="54321",
    test_set_id="67890"
)
```

#### `update_test_result(instance_id: str, status: int, notes: str = None, duration: int = None) -> bool`

Updates the result of a test instance.

**Parameters:**
- `instance_id` (str): Test instance ID
- `status` (int): Test status (0 = PASSED, 1 = FAILED)
- `notes` (str, optional): Test execution notes
- `duration` (int, optional): Execution duration in milliseconds

**Returns:**
- `bool`: True if update successful, False otherwise

**Example:**
```python
success = client.update_test_result(
    instance_id="12345",
    status=0,  # PASSED
    notes="Test completed successfully",
    duration=1500
)
```

#### `get_or_create_test_set(name: str, description: str = None) -> Optional[str]`

Gets an existing test set by name or creates a new one.

**Parameters:**
- `name` (str): Test set name
- `description` (str, optional): Test set description

**Returns:**
- `str`: Test set ID if successful
- `None`: If operation failed

**Example:**
```python
test_set_id = client.get_or_create_test_set(
    name="Daily Regression Tests",
    description="Automated daily test run"
)
```

### Status Codes

PractiTest uses integer status codes for test results:

| Code | Status | Description |
|------|--------|-------------|
| 0 | PASSED | Test executed successfully |
| 1 | FAILED | Test failed with errors |
| 2 | NO RUN | Test was not executed |
| 3 | BLOCKED | Test was blocked |

### Error Handling

All methods include error handling and will:
- Log errors using the Python logging module
- Return `None` or `False` on failure
- Not raise exceptions for API errors

**Example Error Handling:**
```python
test_data = client.get_test_by_display_id("invalid-id")
if test_data is None:
    print("Test not found or API error occurred")
    # Handle the error case
else:
    # Process the test data
    pass
```

### API Endpoints

The client uses the following PractiTest API endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/projects/{project_id}/sets` | Create test set |
| GET | `/projects/{project_id}/tests` | Get test by display ID |
| POST | `/projects/{project_id}/sets/{set_id}/test-instances` | Create test instance |
| PUT | `/projects/{project_id}/runs/{instance_id}` | Update test result |

### Authentication

The client uses HTTP Basic Authentication:
- Username: Your PractiTest email
- Password: Your PractiTest API token

### Rate Limiting

PractiTest may enforce rate limits on API calls. The client does not implement automatic retry logic, so consider adding delays between operations for large test suites.

### Example: Complete Test Reporting Flow

```python
from utils.practitest_client import PractiTestClient

# Initialize client
client = PractiTestClient(
    email="user@company.com",
    token="your-api-token",
    project_id="12345"
)

# Create test set
test_set_id = client.create_test_set(
    name="API Test Run",
    description="Automated API tests"
)

if test_set_id:
    # Get test by display ID
    test_data = client.get_test_by_display_id("697")
    
    if test_data:
        # Create test instance
        instance_id = client.create_test_instance(
            test_id=test_data["id"],
            test_set_id=test_set_id
        )
        
        if instance_id:
            # Update with test result
            success = client.update_test_result(
                instance_id=instance_id,
                status=0,  # PASSED
                notes="API endpoint responded correctly",
                duration=1200
            )
            
            if success:
                print("Test result reported successfully")
```

## Error Scenarios

### Common API Errors

1. **401 Unauthorized**: Invalid email/token combination
2. **403 Forbidden**: Insufficient permissions
3. **404 Not Found**: Invalid project/test/set ID
4. **422 Unprocessable Entity**: Invalid request data
5. **500 Internal Server Error**: PractiTest service issue

### Network Errors

The client handles network errors gracefully:
- Connection timeouts
- DNS resolution failures
- HTTP connection errors

All network errors are logged and result in `None`/`False` return values.

### Debugging API Calls

Enable debug logging to see detailed API interactions:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# API calls will now show request/response details
client = PractiTestClient(email, token, project_id)
```

This will log:
- Request URLs and payloads
- Response status codes and data
- Error messages and stack traces