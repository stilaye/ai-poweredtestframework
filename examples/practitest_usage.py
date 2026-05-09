"""
Example showing how to use PractiTest integration with pytest.

This example demonstrates:
1. How to mark tests with practitestid
2. Different run scenarios (development vs production)
3. Best practices for test organization
4. Conditional marking based on environment
5. Handling test data and assertions
"""

import pytest
import requests
import os


# Constants for test IDs - better maintainability
class PractiTestIDs:
    USER_LOGIN = 697
    API_HEALTH_CHECK = 698
    DATA_RETRIEVAL = 699
    USER_PROFILE = 700
    AUTHENTICATION = 701


# Development test - no PractiTest marker
@pytest.mark.api
@pytest.mark.smoke
def test_development_health_check(base_url, session):
    """Development test without PractiTest integration."""
    response = session.get(f"{base_url}/api/health")
    assert response.status_code == 200
    assert "status" in response.json()


# Production API tests with PractiTest integration
@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.practitestid(PractiTestIDs.API_HEALTH_CHECK)
def test_api_health_endpoint(base_url, session):
    """Test API health endpoint functionality."""
    response = session.get(f"{base_url}/api/health")
    
    # Validate response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.api
@pytest.mark.critical
@pytest.mark.practitestid(PractiTestIDs.USER_LOGIN)
def test_user_authentication(base_url, session):
    """Test user authentication with valid credentials."""
    login_data = {
        "username": "test_user",
        "password": "test_password"
    }
    
    response = session.post(f"{base_url}/api/auth/login", json=login_data)
    
    # Validate successful authentication
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "user_id" in data
    assert data["status"] == "authenticated"


@pytest.mark.api
@pytest.mark.practitestid(PractiTestIDs.USER_PROFILE)
def test_user_profile_retrieval(base_url, session):
    """Test retrieving user profile information."""
    # Assuming session is authenticated
    response = session.get(f"{base_url}/api/user/profile")
    
    # Validate profile data
    assert response.status_code == 200
    profile = response.json()
    assert "user_id" in profile
    assert "email" in profile
    assert "created_at" in profile


@pytest.mark.api
@pytest.mark.data
@pytest.mark.practitestid(PractiTestIDs.DATA_RETRIEVAL)
def test_data_retrieval_with_pagination(base_url, session):
    """Test data retrieval with pagination parameters."""
    params = {
        "page": 1,
        "limit": 10,
        "sort": "created_at"
    }
    
    response = session.get(f"{base_url}/api/data", params=params)
    
    # Validate paginated response
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert len(data["items"]) <= 10


# Conditional marking based on environment
@pytest.mark.api
@pytest.mark.practitestid(PractiTestIDs.AUTHENTICATION) if os.getenv("ENV") == "production" else pytest.mark.skip
def test_production_only_authentication_flow(base_url, session):
    """Test that only runs in production environment."""
    # This test only gets PractiTest reporting in production
    response = session.get(f"{base_url}/api/auth/validate")
    assert response.status_code == 200


# Example of test that might fail - good for demonstrating error reporting
@pytest.mark.api
@pytest.mark.practitestid(702)
def test_api_error_handling():
    """Test that demonstrates error reporting to PractiTest."""
    # This test intentionally fails to show error reporting
    response = requests.get("https://httpbin.org/status/404")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


# Test with parametrization and PractiTest integration
@pytest.mark.api
@pytest.mark.practitestid(703)
@pytest.mark.parametrize("endpoint,expected_status", [
    ("/api/health", 200),
    ("/api/version", 200),
    ("/api/status", 200),
])
def test_multiple_endpoints(base_url, session, endpoint, expected_status):
    """Test multiple endpoints with parametrization."""
    response = session.get(f"{base_url}{endpoint}")
    assert response.status_code == expected_status


# Test with custom fixtures
@pytest.fixture
def api_headers():
    """Fixture providing common API headers."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "PyTest-Automation/1.0"
    }


@pytest.mark.api
@pytest.mark.practitestid(704)
def test_with_custom_headers(base_url, session, api_headers):
    """Test using custom headers fixture."""
    response = session.get(f"{base_url}/api/info", headers=api_headers)
    assert response.status_code == 200
    assert response.headers.get("Content-Type") == "application/json"


# Test with setup and teardown
@pytest.mark.api
@pytest.mark.practitestid(705)
def test_resource_creation_and_cleanup(base_url, session):
    """Test that creates and cleans up resources."""
    # Setup: Create test resource
    create_data = {"name": "test_resource", "type": "temporary"}
    create_response = session.post(f"{base_url}/api/resources", json=create_data)
    assert create_response.status_code == 201
    
    resource_id = create_response.json()["id"]
    
    try:
        # Test: Verify resource exists
        get_response = session.get(f"{base_url}/api/resources/{resource_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "test_resource"
        
    finally:
        # Cleanup: Delete test resource
        delete_response = session.delete(f"{base_url}/api/resources/{resource_id}")
        assert delete_response.status_code == 204


"""
Usage Examples:

1. Development/local testing (no PractiTest reporting):
   pytest --env=dev examples/practitest_usage.py

2. QA testing with PractiTest reporting:
   pytest --env=qa --practitest examples/practitest_usage.py
   
3. Production testing with PractiTest reporting:
   pytest --env=prod --practitest examples/practitest_usage.py

4. Run only marked tests:
   pytest --env=qa --practitest -m "api and smoke" examples/practitest_usage.py

5. Run specific test patterns:
   pytest --env=qa --practitest -k "health or auth" examples/practitest_usage.py

6. Run with verbose output and logging:
   pytest -v --env=qa --practitest --log-cli-level=INFO examples/practitest_usage.py

7. Run and generate HTML report:
   pytest --env=qa --practitest --html=report.html examples/practitest_usage.py

Integration Behavior:
- Without --practitest: All tests run normally, no PractiTest interaction
- With --practitest but no marked tests: Plugin disables itself with info message
- With --practitest and marked tests: Creates test set and reports results
- Plugin gracefully handles missing credentials or API errors

Best Practices Demonstrated:

1. **ID Management**: Use constants for PractiTest IDs (PractiTestIDs class)
2. **Selective Marking**: Only mark stable, production-ready tests
3. **Environment Awareness**: Conditional marking based on environment
4. **Clear Descriptions**: Descriptive test names and docstrings
5. **Proper Assertions**: Meaningful assertions with good error messages
6. **Resource Management**: Proper setup/cleanup in tests
7. **Parameterization**: Using pytest parameters with PractiTest integration
8. **Error Handling**: Demonstrating both success and failure scenarios

Configuration Required:

Environment variables in .env file:
PRACTITEST_EMAIL=your-email@company.com
PRACTITEST_TOKEN=your-api-token
PRACTITEST_PROJECT_ID=your-project-id

Test Environment Variables:
QA_BASE_URL=https://api-qa.example.com
QA_SESSION_ID=your-qa-session-id
PROD_BASE_URL=https://api.example.com
PROD_SESSION_ID=your-prod-session-id
"""