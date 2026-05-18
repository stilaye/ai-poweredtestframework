---
name: integration-mock-builder
description: >
  Generate WireMock stubs or pytest-httpserver fixtures for out-of-process API mocking
  at the integration test level. Trigger for "mock this service", "stub this API",
  "WireMock setup", "I don't have a live endpoint", "mock downstream service",
  "integration test without real server", "record and replay". Background: Swapnil
  used WireMock at Experian for consumer credit API mocking.
  Use this for integration-level mocking. For unit-level (requests/httpx), use openapi-pytest-builder mock mode.
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


# Integration Mock Builder Skill

## Who this is for
Swapnil Tilaye — Python-first SDET. WireMock experience from Experian.
Tools: WireMock (primary), pytest-httpserver (lightweight fallback), vcrpy (record/replay).

---

## Step 1: Choose the right tool

Ask if not clear:
> "Do you need a persistent stub server (WireMock), a lightweight in-test server (pytest-httpserver), or record-and-replay from a real API (vcrpy)?"

| Tool | When to use |
|---|---|
| **WireMock** | Standalone stub server, multiple services, Docker-friendly, matches Experian pattern |
| **pytest-httpserver** | Simple, spun up per test, no external process needed |
| **vcrpy** | Record real API once, replay forever in CI — great for third-party APIs |

---

## WIREMOCK MODE

### Setup — Docker (recommended for CI)
```yaml
# docker-compose.yml
services:
  wiremock:
    image: wiremock/wiremock:latest
    ports:
      - "8080:8080"
    volumes:
      - ./wiremock/mappings:/home/wiremock/mappings
      - ./wiremock/__files:/home/wiremock/__files
    command: --verbose
```

### Stub mapping files (generated per endpoint)
```json
// wiremock/mappings/{resource}_get.json
{
  "request": {
    "method": "GET",
    "urlPattern": "/api/v1/resources/([0-9]+)"
  },
  "response": {
    "status": 200,
    "headers": {
      "Content-Type": "application/json"
    },
    "jsonBody": {
      "id": 1,
      "name": "Mocked Resource",
      "status": "active"
    }
  }
}
```

### Stub for error scenarios
```json
// wiremock/mappings/{resource}_not_found.json
{
  "request": {
    "method": "GET",
    "urlPattern": "/api/v1/resources/99999"
  },
  "response": {
    "status": 404,
    "jsonBody": {"error": "Resource not found"}
  }
}
```

### Stub for auth failure
```json
{
  "request": {
    "method": "GET",
    "url": "/api/v1/resources/1",
    "headers": {
      "Authorization": {"absent": true}
    }
  },
  "response": {
    "status": 401,
    "jsonBody": {"error": "Unauthorized"}
  }
}
```

### pytest conftest for WireMock
```python
import pytest
import requests
import subprocess
import time

WIREMOCK_URL = "http://localhost:8080"

@pytest.fixture(scope="session", autouse=True)
def wiremock_server():
    """Start WireMock via Docker Compose."""
    subprocess.run(["docker-compose", "up", "-d", "wiremock"], check=True)
    # Wait for server to be ready
    for _ in range(10):
        try:
            requests.get(f"{WIREMOCK_URL}/__admin/health")
            break
        except:
            time.sleep(1)
    yield WIREMOCK_URL
    subprocess.run(["docker-compose", "down"], check=True)

@pytest.fixture
def reset_wiremock(wiremock_server):
    """Reset request log between tests."""
    yield
    requests.post(f"{wiremock_server}/__admin/requests/reset")
```

### Verify WireMock was called
```python
def test_{endpoint}_was_called(wiremock_server, client):
    client.get(f"{wiremock_server}/api/v1/resources/1")

    # Verify stub was hit
    verify_response = requests.post(
        f"{wiremock_server}/__admin/requests/count",
        json={"method": "GET", "url": "/api/v1/resources/1"}
    )
    assert verify_response.json()["count"] == 1
```

---

## PYTEST-HTTPSERVER MODE

```python
import pytest
from pytest_httpserver import HTTPServer

@pytest.fixture
def mock_api(httpserver: HTTPServer):
    httpserver.expect_request(
        "/api/v1/resources/1",
        method="GET"
    ).respond_with_json(
        {"id": 1, "name": "Mocked Resource"},
        status=200
    )
    return httpserver.url_for("/")

def test_{resource}_with_mock(mock_api, client):
    response = client.get(f"{mock_api}api/v1/resources/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
```

---

## VCRPY MODE (record and replay)

```python
import vcr
import requests

@vcr.use_cassette("cassettes/{endpoint_name}.yaml")
def test_{endpoint}_recorded(client, auth_headers):
    """
    First run: records real HTTP interaction to cassette file.
    Subsequent runs: replays from cassette — no real network call.
    Commit cassette files to version control.
    """
    response = client.get("/api/v1/resources/1", headers=auth_headers)
    assert response.status_code == 200

# conftest.py — configure vcrpy globally
@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": ["authorization"],    # strip auth from cassettes
        "record_mode": "none",                  # "new_episodes" to re-record
        "cassette_library_dir": "cassettes/"
    }
```

---

## File structure

```
wiremock/
  mappings/
    {resource}_get.json
    {resource}_post.json
    {resource}_not_found.json
    {resource}_unauthorized.json
  __files/
    {large_response_body}.json    → for responses too large for inline JSON
cassettes/
  {endpoint_name}.yaml            → vcrpy recorded interactions
tests/
  conftest.py                     → WireMock/httpserver fixtures
  test_{resource}_integration.py  → integration tests using mocks
docker-compose.yml                → WireMock container definition
```

---

## Output rules

- Default to WireMock — matches Experian pattern, most portable
- Always generate stubs for: happy path, 404, 401, 422, 500
- vcrpy cassettes: always strip auth headers before committing
- pytest-httpserver: use for simple single-service cases only
- Always include Docker Compose file when generating WireMock setup
- Flag stateful scenarios (e.g. create then retrieve): `# TODO: use WireMock stateful scenarios — see /admin/scenarios`
