# PractiTest Integration Guide

## Overview

The PractiTest integration provides seamless test result reporting from your pytest automation framework directly to PractiTest. This integration is designed to be optional and non-intrusive - tests run normally without the integration unless explicitly enabled.

## Architecture

The integration consists of two main components:

### 1. PractiTest Client (`utils/practitest_client.py`)
- Direct API interface to PractiTest v2 API
- Handles authentication and HTTP requests
- Provides methods for test set management and result reporting

### 2. Pytest Plugin (`utils/practitest_plugin.py`)
- Implements pytest hook system for seamless integration
- Automatically activates only when conditions are met
- Manages test lifecycle and result reporting

## Quick Start

### 1. Setup Credentials

Add your PractiTest credentials to the `.env` file:

```bash
PRACTITEST_EMAIL=your-email@company.com
PRACTITEST_TOKEN=your-api-token
PRACTITEST_PROJECT_ID=your-project-id
```

### 2. Mark Your Tests

Add the `@pytest.mark.practitestid` marker to tests you want to report:

```python
import pytest

@pytest.mark.practitestid(697)
def test_api_endpoint():
    """Test that will be reported to PractiTest."""
    response = requests.get("https://api.example.com/health")
    assert response.status_code == 200
```

### 3. Run Tests with Integration

Enable PractiTest integration with the `--practitest` flag:

```bash
# With PractiTest integration
pytest --env=qa --practitest tests/

# Without PractiTest integration (normal pytest)
pytest --env=qa tests/
```

## Configuration

### Environment Variables

The integration requires three environment variables that can be set in your `.env` file:

| Variable | Description | Example |
|----------|-------------|---------|
| `PRACTITEST_EMAIL` | Your PractiTest account email | `user@company.com` |
| `PRACTITEST_TOKEN` | Your PractiTest API token | `abc123def456...` |
| `PRACTITEST_PROJECT_ID` | Target PractiTest project ID | `12345` |

### Getting Your API Token

1. Log into PractiTest
2. Go to Account Settings → API Tokens
3. Generate a new token or use an existing one
4. Copy the token to your `.env` file

### Finding Your Project ID

1. Navigate to your project in PractiTest
2. The project ID is visible in the URL: `https://api.practitest.com/projects/{PROJECT_ID}`
3. Use this ID in your configuration

## Test Marking

### Basic Usage

Mark individual tests with their PractiTest display ID:

```python
@pytest.mark.practitestid(697)
def test_user_login():
    # Test implementation
    pass
```

### Multiple Markers

Tests can have multiple markers - only `practitestid` affects PractiTest integration:

```python
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.practitestid(698)
def test_critical_endpoint():
    # Test implementation
    pass
```

### Conditional Marking

You can conditionally apply markers based on environment:

```python
import os
import pytest

# Only mark for production environments
production_marker = pytest.mark.practitestid(699) if os.getenv("ENV") == "prod" else pytest.mark.skip

@production_marker
def test_production_feature():
    # Test implementation
    pass
```

## Integration Behavior

### Activation Conditions

The PractiTest integration only activates when **ALL** of the following are true:

1. `--practitest` flag is provided
2. Valid credentials are available (env vars or `.env` file)
3. At least one test has a `@pytest.mark.practitestid` marker

### Execution Flow

1. **Configuration Phase**: Loads credentials and checks activation conditions
2. **Collection Phase**: Identifies tests with PractiTest markers
3. **Session Start**: Creates a test set in PractiTest with metadata
4. **Test Setup**: Creates test instances for each marked test
5. **Test Execution**: Captures test results (PASSED/FAILED)
6. **Session Finish**: Reports all results to PractiTest

### Test Set Management

Each test run creates a new test set with the following naming pattern:

```
Automated Test Run-{node_version}-{os_name}-{timestamp}
```

Example: `Automated Test Run-1.2.3-Ubuntu 20.04-2024-01-15_14-30-45`

## Result Reporting

### Status Mapping

| Test Result | PractiTest Status | Description |
|-------------|-------------------|-------------|
| PASSED | 0 (PASSED) | Test completed successfully |
| FAILED | 1 (FAILED) | Test failed with exception |

### Result Details

For each test, the following information is reported:

- **Status**: Pass/Fail based on test outcome
- **Notes**: Success message or exception details
- **Duration**: Test execution time in milliseconds
- **Execution Context**: Node version, OS, timestamp

### Example Result Notes

**Passed Test:**
```
Test passed successfully
```

**Failed Test:**
```
Test failed: AssertionError: Expected status code 200, got 404
```

## Command Line Usage

### Basic Commands

```bash
# Run all tests with PractiTest integration
pytest --env=qa --practitest tests/

# Run specific test file
pytest --env=qa --practitest tests/test_api_mp_endpoint.py

# Run with verbose output
pytest -v --env=qa --practitest tests/

# Run and save output to log
pytest --env=qa --practitest tests/ | tee test_output.log
```

### Filtering Tests

```bash
# Run only tests with specific markers
pytest --env=qa --practitest -m "api and not slow" tests/

# Run tests matching pattern
pytest --env=qa --practitest -k "endpoint" tests/

# Run specific test by name
pytest --env=qa --practitest tests/test_api_mp_endpoint.py::test_get_node_details
```

### Development vs Production

```bash
# Development (no PractiTest reporting)
pytest --env=dev tests/

# Production (with PractiTest reporting)
pytest --env=prod --practitest tests/
```

## Troubleshooting

### Common Issues

#### 1. Integration Not Activating

**Symptoms:** Tests run but no PractiTest activity logged

**Solutions:**
- Verify `--practitest` flag is included
- Check that at least one test has `@pytest.mark.practitestid` marker
- Confirm credentials are properly set

#### 2. Authentication Errors

**Symptoms:** "Failed to initialize PractiTest client" error

**Solutions:**
- Verify email and token are correct
- Check that token has appropriate permissions
- Ensure project ID exists and is accessible

#### 3. Test Not Found in PractiTest

**Symptoms:** Warning "Test with display ID XXX not found"

**Solutions:**
- Verify the display ID exists in your PractiTest project
- Check that the test hasn't been deleted or moved
- Ensure you're using the correct project ID

#### 4. Network/Connection Issues

**Symptoms:** Timeout or connection errors

**Solutions:**
- Check internet connectivity
- Verify PractiTest service status
- Consider firewall or proxy settings

### Debug Logging

Enable debug logging to troubleshoot issues:

```bash
pytest --env=qa --practitest --log-cli-level=DEBUG tests/
```

This will show detailed information about:
- Credential loading
- API requests and responses
- Test set creation
- Result reporting

### Environment Variable Debug

Verify your environment variables are loaded correctly:

```python
import os
from dotenv import load_dotenv

load_dotenv()
print(f"Email: {os.getenv('PRACTITEST_EMAIL')}")
print(f"Token: {'*' * len(os.getenv('PRACTITEST_TOKEN', ''))} (length: {len(os.getenv('PRACTITEST_TOKEN', ''))})")
print(f"Project ID: {os.getenv('PRACTITEST_PROJECT_ID')}")
```

## Best Practices

### 1. Selective Test Marking

Only mark stable, production-ready tests for PractiTest integration:

```python
# Good: Stable API test
@pytest.mark.practitestid(697)
def test_critical_api_endpoint():
    pass

# Avoid: Experimental or flaky test
def test_experimental_feature():
    pass
```

### 2. Environment Separation

Use different markers or conditional logic for different environments:

```python
import os
import pytest

# Only report production tests to PractiTest
if os.getenv("ENV") == "production":
    production_test = pytest.mark.practitestid(698)
else:
    production_test = lambda func: func

@production_test
def test_production_endpoint():
    pass
```

### 3. Meaningful Test Names

Use descriptive test names that will be clear in PractiTest reports:

```python
# Good: Clear, descriptive name
@pytest.mark.practitestid(699)
def test_user_authentication_with_valid_credentials():
    pass

# Avoid: Vague or technical name
@pytest.mark.practitestid(700)
def test_auth():
    pass
```

### 4. Consistent Display ID Management

Maintain a mapping of display IDs to test functions:

```python
# Consider creating a constants file
PRACTITEST_IDS = {
    "USER_LOGIN": 697,
    "API_HEALTH": 698,
    "DATA_RETRIEVAL": 699,
}

@pytest.mark.practitestid(PRACTITEST_IDS["USER_LOGIN"])
def test_user_login():
    pass
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Test with PractiTest
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests with PractiTest
        env:
          PRACTITEST_EMAIL: ${{ secrets.PRACTITEST_EMAIL }}
          PRACTITEST_TOKEN: ${{ secrets.PRACTITEST_TOKEN }}
          PRACTITEST_PROJECT_ID: ${{ secrets.PRACTITEST_PROJECT_ID }}
        run: pytest --env=qa --practitest tests/
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    environment {
        PRACTITEST_EMAIL = credentials('practitest-email')
        PRACTITEST_TOKEN = credentials('practitest-token')
        PRACTITEST_PROJECT_ID = credentials('practitest-project-id')
    }
    
    stages {
        stage('Test') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pytest --env=qa --practitest tests/'
            }
        }
    }
}
```

## API Reference

For detailed API documentation, see:
- [PractiTest Client API](practitest-api-reference.md)
- [Plugin Hooks Reference](practitest-plugin-hooks.md)

## Support

For issues related to:
- **PractiTest API**: Contact PractiTest support
- **Integration code**: Create an issue in this repository
- **Test framework**: See pytest documentation