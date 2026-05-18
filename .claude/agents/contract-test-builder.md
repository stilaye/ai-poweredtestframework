---
name: contract-test-builder
description: "Use this agent when asked to generate consumer-driven contract tests using Pact, or snapshot-based drift detection. Examples: <example>Context: Two microservices need contract validation. user: 'Write contract tests between our auth service and user service' assistant: 'I will use the contract-test-builder agent to generate Pact consumer and provider test files.' <commentary>Multi-service contract validation — invoke contract-test-builder.</commentary></example>"
color: green
---


# Contract Test Builder Skill

## Who this is for
Swapnil Tilaye — Python-first SDET. Microservices background from F5 Networks and EdgeQ.
Libraries: `pact-python` (Pact mode), `responses` + JSON snapshot (Snapshot mode).

---

## Step 1: Determine mode

Ask if not clear from context:
> "Do you have two services/teams involved (Pact mode), or are you detecting drift on a single API (Snapshot mode)?"

- **Pact mode** → consumer defines expectations, provider verifies them
- **Snapshot mode** → record response once, alert when shape changes

---

## PACT MODE

### File structure
```
consumer/
  test_consumer_{provider_name}.py   → defines interactions, generates pact JSON
pacts/
  {consumer}-{provider}.json         → generated contract file (commit to repo)
provider/
  test_provider_verify.py            → loads contract, verifies provider
```

### Consumer side
```python
import pytest
from pact import Consumer, Provider

@pytest.fixture(scope="session")
def pact():
    pact = Consumer("ConsumerService").has_pact_with(
        Provider("ProviderService"),
        pact_dir="./pacts"
    )
    pact.start_service()
    yield pact
    pact.stop_service()

def test_get_resource_exists(pact):
    expected = {"id": 1, "name": "Test Resource", "status": "active"}

    (pact
        .given("resource 1 exists")
        .upon_receiving("a request for resource 1")
        .with_request("GET", "/resources/1")
        .will_respond_with(200, body=expected))

    with pact:
        result = requests.get(f"{pact.uri}/resources/1")
        assert result.json() == expected

def test_get_resource_not_found(pact):
    (pact
        .given("resource 99999 does not exist")
        .upon_receiving("a request for nonexistent resource")
        .with_request("GET", "/resources/99999")
        .will_respond_with(404, body={"error": "not found"}))

    with pact:
        result = requests.get(f"{pact.uri}/resources/99999")
        assert result.status_code == 404
```

### Provider states to always cover
- "resource exists" → 200
- "resource does not exist" → 404
- "unauthorized request" → 401
- "invalid input" → 422
- "server error" → 500

### Provider verification side
```python
from pact import Verifier

def test_provider_verify():
    verifier = Verifier(
        provider="ProviderService",
        provider_base_url="http://localhost:8080"
    )
    output, _ = verifier.verify_pacts(
        "./pacts/ConsumerService-ProviderService.json",
        provider_states_setup_url="http://localhost:8080/_pact/provider-states"
    )
    assert output == 0, "Provider failed to satisfy consumer contract"
```

---

## SNAPSHOT MODE (drift detection)

Use when: no second team, just want to catch silent API changes over time.

### Step 1: Record snapshot
```python
import json
import hashlib
from pathlib import Path

def record_snapshot(response_body, snapshot_name):
    snapshot_path = Path(f"snapshots/{snapshot_name}.json")
    snapshot_path.parent.mkdir(exist_ok=True)
    snapshot_path.write_text(json.dumps(response_body, indent=2))
```

### Step 2: Compare on each run
```python
def test_{endpoint_name}_no_drift(client, auth_headers):
    response = client.get(url, headers=auth_headers)
    current = response.json()
    snapshot_path = Path(f"snapshots/{endpoint_name}.json")

    if not snapshot_path.exists():
        record_snapshot(current, "{endpoint_name}")
        pytest.skip("Snapshot recorded — run again to detect drift")

    previous = json.loads(snapshot_path.read_text())

    # Compare shape (keys) not values
    assert set(current.keys()) == set(previous.keys()), \
        f"Schema drift detected. Added: {set(current.keys()) - set(previous.keys())}, "\
        f"Removed: {set(previous.keys()) - set(current.keys())}"

    # Compare nested types
    for key in previous:
        assert type(current.get(key)) == type(previous[key]), \
            f"Type changed for field '{key}': was {type(previous[key]).__name__}, "\
            f"now {type(current.get(key)).__name__}"
```

### File structure (Snapshot mode)
```
snapshots/
  {endpoint_name}.json     → recorded baseline responses
tests/
  test_drift_{resource}.py → drift detection tests
```

---

## gRPC contract testing

Use Pact gRPC plugin (Pact v4+):
```python
# Note: requires pact-python v2+ with gRPC plugin
# Flag for user if pact-python version < 2.0
# Fallback: use snapshot mode on proto message shapes
```

## GraphQL contract testing

Use schema diffing approach:
```python
from graphql import build_schema, find_breaking_changes

def test_no_breaking_schema_changes():
    old_schema = build_schema(Path("snapshots/schema_baseline.graphql").read_text())
    new_schema = build_schema(fetch_current_schema())
    breaking = find_breaking_changes(old_schema, new_schema)
    assert len(breaking) == 0, f"Breaking schema changes detected: {breaking}"
```

---

## Output rules

- Always ask which mode before generating (Pact vs Snapshot)
- Pact mode: always generate both consumer AND provider files
- Snapshot mode: always include skip logic for first run (no snapshot yet)
- Never hardcode provider URLs — use `os.getenv()`
- Flag gRPC Pact as requiring pact-python v2+ with comment
