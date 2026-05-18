---
name: openapi-pytest-builder
description: >
  Generate a ready-to-run pytest test suite from an OpenAPI spec (YAML or JSON).
  Trigger when given an OpenAPI/Swagger spec file, URL, or pasted content and asked
  to generate API tests, test coverage, or a test suite. Also trigger for phrases like
  "write tests for this API", "generate pytest from swagger", "test this endpoint",
  "create API test coverage". Accepts .yaml, .json, or pasted spec text.
  Always generates both live-endpoint mode (requests/httpx) and mock mode (responses/respx).
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


# OpenAPI Pytest Builder Skill

## Who this is for
Swapnil Tilaye — Python-first SDET. Default HTTP client: `requests`.
Use `httpx` only if spec involves async endpoints or user explicitly asks.

---

## Step 1: Parse the spec

Accept input as:
- Pasted YAML or JSON text
- Uploaded `.yaml` / `.json` file at `/mnt/user-data/uploads/`
- URL → fetch with web_fetch tool

Extract per endpoint:
- Method (GET/POST/PUT/DELETE/PATCH)
- Path + path parameters
- Query parameters (required vs optional)
- Request body schema (if POST/PUT/PATCH)
- Response schemas per status code
- Auth requirements (Bearer, API key, OAuth)
- Tags (used for grouping test files)

---

## Step 2: Determine mode

Ask if not specified:
> "Do you have a live/sandbox endpoint to test against, or do you need mocked tests?"

- **Live mode** → use `requests` directly, real HTTP calls
- **Mock mode** → wrap with `responses` library (for `requests`) or `respx` (for `httpx`)
- **Both** → generate live tests + a mock variant with `@pytest.mark.mock` marker

---

## Step 3: Generate file structure

```
tests/
  conftest.py              → base_url fixture, auth headers, shared setup
  test_{tag_name}.py       → one file per OpenAPI tag/resource group
  mock/
    test_{tag_name}_mock.py  → mock mode variants (if requested)
```

---

## Step 4: Test cases per endpoint

Generate these test cases for every endpoint:

### Happy path
```python
def test_{method}_{resource}_success(client, auth_headers):
    """Happy path — valid request, assert 200/201 + response schema."""
    response = client.{method}(url, headers=auth_headers, json=payload)
    assert response.status_code == 200
    assert_schema(response.json(), expected_schema)
```

### Missing required fields (POST/PUT only)
```python
@pytest.mark.parametrize("missing_field", ["field1", "field2"])
def test_{method}_{resource}_missing_required(client, auth_headers, missing_field):
    payload = valid_payload.copy()
    del payload[missing_field]
    response = client.post(url, headers=auth_headers, json=payload)
    assert response.status_code == 422
```

### Invalid data types
```python
def test_{method}_{resource}_invalid_types(client, auth_headers):
    payload = {**valid_payload, "integer_field": "not_an_int"}
    response = client.post(url, headers=auth_headers, json=payload)
    assert response.status_code == 422
```

### Auth failures
```python
def test_{method}_{resource}_no_auth(client):
    response = client.{method}(url)
    assert response.status_code == 401

def test_{method}_{resource}_invalid_token(client):
    response = client.{method}(url, headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
```

### Not found (GET with ID)
```python
def test_get_{resource}_not_found(client, auth_headers):
    response = client.get(f"{url}/nonexistent_id_99999", headers=auth_headers)
    assert response.status_code == 404
```

---

## Step 5: conftest.py structure

```python
import pytest
import requests

@pytest.fixture(scope="session")
def base_url():
    return "https://api.example.com/v1"  # from spec servers[]

@pytest.fixture(scope="session")
def auth_headers():
    # Bearer token — replace with env var in CI
    return {"Authorization": f"Bearer {os.getenv('API_TOKEN')}"}

@pytest.fixture
def client():
    session = requests.Session()
    yield session
    session.close()

def assert_schema(response_body, schema):
    """Validate response against jsonschema."""
    from jsonschema import validate
    validate(instance=response_body, schema=schema)
```

---

## Step 6: Mock mode (when no live endpoint)

Use `responses` library to intercept `requests` calls:

```python
import responses as rsps

@rsps.activate
def test_{method}_{resource}_mocked(client, auth_headers):
    rsps.add(
        rsps.GET,
        "https://api.example.com/v1/resource",
        json={"id": 1, "name": "test"},
        status=200
    )
    response = client.get(url, headers=auth_headers)
    assert response.status_code == 200
```

For `httpx` async, use `respx` with same pattern but `async def` + `await`.

---

## Output rules

- One test file per OpenAPI tag — not one file per endpoint
- Use `pytest.mark.parametrize` for data-driven cases
- All env vars via `os.getenv()` — no hardcoded credentials
- Include `requirements.txt` snippet at top of conftest.py as a comment
- No test cases for endpoints with no defined response schema
- Flag endpoints with missing schema as a comment: `# TODO: no response schema defined`
