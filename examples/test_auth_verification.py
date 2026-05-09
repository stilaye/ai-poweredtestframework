import pytest
import os

@pytest.mark.api
def test_verify_bearer_token_auth(session, common_headers, common_cookies):
    """Verify that tests are using Bearer token authentication, not cookies."""
    
    # Check that Authorization header exists with Bearer token
    assert "Authorization" in session.headers, "Authorization header missing from session"
    assert session.headers["Authorization"].startswith("Bearer "), f"Expected Bearer token, got: {session.headers.get('Authorization', 'None')}"
    
    # Check that session cookies are empty or don't contain sign-in session
    sign_in_cookie = session.cookies.get("__Secure-signInSessionId")
    
    # If api_token.txt exists, cookies should be empty
    api_token_file_exists = os.path.exists("api_token.txt") and os.path.getsize("api_token.txt") > 0
    
    if api_token_file_exists:
        assert sign_in_cookie is None, f"Expected no session cookies when using api_token.txt, but found: {sign_in_cookie}"
        print("✅ Using Bearer token authentication from api_token.txt")
    else:
        # When no api_token.txt, both Bearer token and cookies should be present
        assert sign_in_cookie is not None, "Expected session cookie when not using api_token.txt"
        print("✅ Using Bearer token authentication from Secret Manager (with fallback cookies)")
    
    print(f"🔑 Authorization header: {session.headers['Authorization'][:20]}...")

@pytest.mark.api
def test_api_call_with_bearer_token(base_url, session):
    """Test an actual API call to ensure Bearer token works."""
    
    # Make a simple API call
    response = session.get(f"{base_url}/api/system-info")
    
    # Print auth details for debugging
    print(f"🔑 Using auth header: {session.headers.get('Authorization', 'None')[:20]}...")
    print(f"🍪 Session cookies: {list(session.cookies.keys())}")
    print(f"📡 Response status: {response.status_code}")
    
    # Should get successful response with Bearer token
    assert response.status_code == 200, f"API call failed with Bearer token: {response.status_code}"
    
    print("✅ API call successful with Bearer token authentication")