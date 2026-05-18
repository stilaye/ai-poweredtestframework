---
name: api-security-builder
description: >
  Generate security-focused API test cases based on OWASP API Top 10 from an OpenAPI spec,
  .proto file, or GraphQL schema. Trigger for "write security tests", "OWASP tests",
  "API security testing", "pen test this API", "auth bypass tests", "injection tests",
  "security coverage". Background: Swapnil used OWASP ZAP and bandit at F5 Networks.
---

## Auto-run vs intake

**If a spec exists in `specs/` → run immediately, no questions.**
**Only ask if genuinely blocked:**

| Situation | Ask |
|---|---|
| No spec found anywhere | "Paste your spec, give a path, or provide a URL" (one ask) |
| Multiple specs in `specs/` | "Which spec should I use?" (list them) |
| Mode unclear for REST | "Live endpoint available, or mock mode?" (one ask) |
| Everything clear | Never prompt — just generate |

Never ask more than one question. Never re-ask something already answered in the conversation.

---


# API Security Builder Skill

## Who this is for
Swapnil Tilaye — Python-first SDET. Security testing background from F5 Networks
(OWASP ZAP, distributed microservices, continuous security pipeline).
Libraries: `pytest`, `requests`, `bandit` (static), `OWASP ZAP` Python API (dynamic).

---

## Step 1: Parse spec for security surface

From the spec extract:
- Auth mechanisms (Bearer, API key, OAuth2, Basic)
- Endpoints that accept user input (POST/PUT/PATCH body, query params, path params)
- Endpoints that return sensitive data (PII, credentials, internal IDs)
- Admin or privileged endpoints
- File upload endpoints
- Rate limiting headers (X-RateLimit-*)

---

## Step 2: OWASP API Top 10 coverage

Generate test cases for each applicable category:

### API1 — Broken Object Level Authorization (BOLA)
```python
def test_bola_{resource}(client, user_a_headers, user_b_headers):
    """User A should not access User B's resources."""
    # Create resource as User B
    resource_id = create_resource_as_user_b()
    # Try to access as User A
    response = client.get(f"/resources/{resource_id}", headers=user_a_headers)
    assert response.status_code in [403, 404], \
        f"BOLA vulnerability: User A accessed User B's resource (got {response.status_code})"
```

### API2 — Broken Authentication
```python
@pytest.mark.parametrize("bad_token", [
    "",                          # empty
    "Bearer ",                   # bearer with no token
    "Bearer invalidtoken123",    # invalid token
    "Bearer " + "a" * 500,       # oversized token
    None                         # no auth header
])
def test_broken_auth_{endpoint}(client, bad_token):
    headers = {"Authorization": bad_token} if bad_token else {}
    response = client.get("/protected-endpoint", headers=headers)
    assert response.status_code == 401, \
        f"Auth bypass possible with token: '{bad_token}'"
```

### API3 — Broken Object Property Level Authorization
```python
def test_mass_assignment_{resource}(client, auth_headers):
    """Ensure privileged fields can't be set by regular users."""
    payload = {
        "name": "legitimate value",
        "role": "admin",          # should be ignored
        "is_verified": True,      # should be ignored
        "balance": 999999         # should be ignored
    }
    response = client.post("/resources", json=payload, headers=auth_headers)
    if response.status_code == 201:
        created = response.json()
        assert created.get("role") != "admin", "Mass assignment vulnerability: role field accepted"
        assert created.get("balance") != 999999, "Mass assignment vulnerability: balance field accepted"
```

### API4 — Unrestricted Resource Consumption (Rate Limiting)
```python
def test_rate_limiting_{endpoint}(client, auth_headers):
    """Verify rate limiting is enforced."""
    responses = [
        client.get("/endpoint", headers=auth_headers)
        for _ in range(100)
    ]
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes, \
        "Rate limiting not enforced — 100 requests all succeeded"
```

### API5 — Broken Function Level Authorization
```python
def test_privilege_escalation_admin_endpoint(client, regular_user_headers):
    """Regular user should not access admin endpoints."""
    admin_endpoints = ["/admin/users", "/admin/config", "/internal/metrics"]
    for endpoint in admin_endpoints:
        response = client.get(endpoint, headers=regular_user_headers)
        assert response.status_code in [401, 403], \
            f"Privilege escalation: regular user accessed {endpoint}"
```

### API6 — Unrestricted Access to Sensitive Business Flows
```python
def test_business_flow_abuse_{flow}(client, auth_headers):
    """Verify business flow can't be abused at scale."""
    # Example: coupon code can't be applied 100x
    responses = [
        client.post("/apply-coupon", json={"code": "SAVE10"}, headers=auth_headers)
        for _ in range(10)
    ]
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count == 1, f"Business flow abuse: coupon applied {success_count} times"
```

### API7 — Server Side Request Forgery (SSRF)
```python
@pytest.mark.parametrize("ssrf_payload", [
    "http://169.254.169.254/latest/meta-data/",   # AWS metadata
    "http://localhost:22",                          # internal SSH
    "http://internal-service:8080/admin",           # internal service
    "file:///etc/passwd"                            # local file
])
def test_ssrf_{endpoint}(client, auth_headers, ssrf_payload):
    payload = {"url": ssrf_payload, "callback": ssrf_payload}
    response = client.post("/fetch-url", json=payload, headers=auth_headers)
    assert response.status_code in [400, 403, 422], \
        f"Possible SSRF: server accepted internal URL {ssrf_payload}"
```

### API8 — Security Misconfiguration
```python
def test_security_headers(client):
    """Verify security headers are present."""
    response = client.get("/")
    headers = response.headers
    assert "X-Content-Type-Options" in headers
    assert "X-Frame-Options" in headers
    assert "Strict-Transport-Security" in headers
    assert "Content-Security-Policy" in headers

def test_no_sensitive_data_in_error(client, auth_headers):
    """Error responses should not leak stack traces or internal info."""
    response = client.get("/resources/invalid_id_that_causes_error", headers=auth_headers)
    body = response.text.lower()
    assert "traceback" not in body
    assert "stack trace" not in body
    assert "sql" not in body
    assert "exception" not in body
```

### API9 — Improper Inventory Management
```python
def test_no_debug_endpoints(client):
    """Common debug/dev endpoints should not be exposed in production."""
    debug_endpoints = ["/debug", "/swagger-ui", "/api-docs", "/.env",
                      "/actuator", "/metrics", "/health/detailed"]
    for endpoint in debug_endpoints:
        response = client.get(endpoint)
        assert response.status_code in [401, 403, 404], \
            f"Debug endpoint exposed: {endpoint} returned {response.status_code}"
```

### API10 — Unsafe Consumption of APIs
```python
@pytest.mark.parametrize("injection_payload", [
    "'; DROP TABLE users; --",      # SQL injection
    "<script>alert('xss')</script>", # XSS
    "../../../etc/passwd",           # path traversal
    "${7*7}",                        # template injection
    "{{7*7}}"                        # SSTI
])
def test_injection_{endpoint}(client, auth_headers, injection_payload):
    payload = {"name": injection_payload, "description": injection_payload}
    response = client.post("/resources", json=payload, headers=auth_headers)
    if response.status_code == 201:
        created = response.json()
        assert injection_payload not in str(created), \
            f"Injection payload reflected in response — possible vulnerability"
    # 400/422 = input validation working correctly
    assert response.status_code in [201, 400, 422]
```

---

## gRPC-specific security tests

Generate these when input is a .proto file:

### gRPC Auth failures
```python
@pytest.mark.parametrize("bad_metadata", [
    [],                                          # no metadata
    [("authorization", "Bearer ")],              # empty token
    [("authorization", "Bearer invalidtoken")],  # invalid token
    [("authorization", "Bearer " + "a" * 500)],  # oversized token
])
def test_grpc_broken_auth_{method}(stub, bad_metadata):
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.{MethodName}(valid_request, metadata=bad_metadata)
    assert exc_info.value.code() == grpc.StatusCode.UNAUTHENTICATED
```

### gRPC privilege escalation
```python
def test_grpc_permission_denied_{method}(stub, regular_user_metadata):
    """Regular user calling admin-only RPC should get PERMISSION_DENIED."""
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.AdminOnlyMethod(valid_request, metadata=regular_user_metadata)
    assert exc_info.value.code() == grpc.StatusCode.PERMISSION_DENIED
```

### gRPC oversized payload (resource exhaustion)
```python
def test_grpc_oversized_payload_{method}(stub, auth_metadata):
    """Large payloads should be rejected — not cause server crash."""
    from your_service_pb2 import YourRequest
    oversized_request = YourRequest(
        name="A" * 100000,   # 100KB string
        data=b"B" * 1000000  # 1MB bytes field
    )
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.{MethodName}(oversized_request, metadata=auth_metadata)
    assert exc_info.value.code() in [
        grpc.StatusCode.INVALID_ARGUMENT,
        grpc.StatusCode.RESOURCE_EXHAUSTED
    ]
```

### gRPC metadata injection
```python
@pytest.mark.parametrize("injected_value", [
    "'; DROP TABLE users; --",
    "<script>alert('xss')</script>",
    "../../../etc/passwd"
])
def test_grpc_metadata_injection_{method}(stub, auth_metadata, injected_value):
    """Injected values in metadata should not cause server errors."""
    malicious_metadata = auth_metadata + [("x-user-id", injected_value)]
    try:
        response = stub.{MethodName}(valid_request, metadata=malicious_metadata)
        # If it succeeds, injected value must not appear in response
        assert injected_value not in str(response)
    except grpc.RpcError as e:
        assert e.code() in [
            grpc.StatusCode.INVALID_ARGUMENT,
            grpc.StatusCode.UNAUTHENTICATED
        ]
```

---

## GraphQL-specific security tests

Generate these when input is a .graphql schema:

### GraphQL introspection disabled in production
```python
def test_graphql_introspection_disabled(execute):
    """Introspection should be disabled in production — leaks schema."""
    with pytest.raises(Exception) as exc_info:
        execute("{ __schema { types { name } } }")
    assert "introspection" in str(exc_info.value).lower() or \
           "disabled" in str(exc_info.value).lower(), \
        "GraphQL introspection is enabled — schema is exposed"
```

### GraphQL deeply nested query (DoS)
```python
def test_graphql_query_depth_limit(execute):
    """Deeply nested queries should be rejected — prevents DoS."""
    deep_query = "{ user { posts { comments { author { posts { comments { author { id } } } } } } } }"
    with pytest.raises(Exception) as exc_info:
        execute(deep_query)
    assert "depth" in str(exc_info.value).lower() or \
           "complexity" in str(exc_info.value).lower() or \
           "limit" in str(exc_info.value).lower(), \
        "No query depth limit — vulnerable to DoS via deeply nested queries"
```

### GraphQL field-level authorization
```python
def test_graphql_field_auth_sensitive_data(execute, regular_user_token):
    """Regular users should not access sensitive fields."""
    result = execute("""
        query {
            user(id: "other_user_id") {
                id
                email
                ssn          # sensitive — should be null or error
                creditCard   # sensitive — should be null or error
            }
        }
    """)
    user = result.get("user", {})
    assert user.get("ssn") is None, "SSN exposed to unauthorized user"
    assert user.get("creditCard") is None, "Credit card exposed to unauthorized user"
```

### GraphQL batch query abuse
```python
def test_graphql_batch_limit(gql_client):
    """Batch queries should have a limit — prevents brute force via batching."""
    # Send 100 queries in one batch request
    batch = [{"query": f'{{ user(id: "{i}") {{ id email }} }}'}
             for i in range(100)]
    response = requests.post(
        os.getenv("GRAPHQL_ENDPOINT"),
        json=batch,
        headers={"Authorization": f"Bearer {os.getenv('GQL_TOKEN')}"}
    )
    # Should reject large batches
    assert response.status_code in [400, 429], \
        f"Batch query abuse possible — 100 queries accepted (status {response.status_code})"
```

### GraphQL injection via variables
```python
@pytest.mark.parametrize("injection", [
    "'; DROP TABLE users; --",
    "${7*7}",
    "{{7*7}}"
])
def test_graphql_variable_injection(execute, injection):
    """Variables should be sanitized — not interpolated into queries."""
    result = execute("""
        query SearchProducts($name: String!) {
            products(name: $name) { id name }
        }
    """, variables={"name": injection})
    # Should return empty results, not an error or reflected injection
    products = result.get("products", [])
    for product in products:
        assert injection not in str(product), \
            f"Injection payload reflected in response"
```

---

## Step 3: Static analysis

Add `bandit` scan as a pytest fixture check:
```python
def test_static_security_scan():
    """Run bandit static analysis on source code."""
    import subprocess
    result = subprocess.run(
        ["bandit", "-r", "src/", "-ll", "--exit-zero"],
        capture_output=True, text=True
    )
    high_severity = result.stdout.count("Severity: High")
    assert high_severity == 0, f"Bandit found {high_severity} high severity issues:
{result.stdout}"
```

---

## Output rules

- Always cover all 10 OWASP API categories — skip with `pytest.mark.skip(reason=)` if not applicable
- Use `pytest.mark.security` marker on all tests for easy CI filtering
- Never hardcode real credentials — use clearly fake test values
- Flag endpoints handling PII with extra BOLA + property-level auth tests
- Add `# OWASP API{N}` comment on every test class for traceability
