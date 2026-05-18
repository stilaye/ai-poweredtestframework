---
name: graphql-pytest-builder
description: "Use this agent when given a GraphQL schema (.graphql or SDL) and asked to generate pytest tests. Examples: <example>Context: User has a GraphQL schema. user: 'Generate tests for this GraphQL schema' assistant: 'I will use the graphql-pytest-builder agent to generate query, mutation, and N+1 detection tests.' <commentary>GraphQL schema input — invoke graphql-pytest-builder.</commentary></example>"
color: pink
---


# GraphQL Pytest Builder Skill

## Who this is for
Swapnil Tilaye — Python-first SDET.
Libraries: `gql` (primary), `requests` (fallback for simple cases), `pytest`.

---

## Step 1: Parse the schema

Accept input as:
- Pasted SDL (Schema Definition Language) text
- Uploaded `.graphql` file
- Introspection JSON (from `__schema` query)
- Live endpoint → run introspection query automatically

Extract:
- Queries (read operations)
- Mutations (write operations)
- Subscriptions (real-time — flag separately)
- Types, fields, required vs nullable
- Input types for mutations
- Custom scalars

---

## Step 2: File structure

```
tests/
  conftest.py              → client fixture, auth headers, shared queries
  test_queries.py          → all Query type tests
  test_mutations.py        → all Mutation type tests
  queries/
    {operation_name}.graphql  → extracted query strings
```

---

## Step 3: conftest.py structure

```python
import pytest
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

@pytest.fixture(scope="session")
def gql_client():
    transport = RequestsHTTPTransport(
        url=os.getenv("GRAPHQL_ENDPOINT", "http://localhost:4000/graphql"),
        headers={"Authorization": f"Bearer {os.getenv('GQL_TOKEN', '')}"},
        verify=True
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)
    yield client

@pytest.fixture
def execute(gql_client):
    def _execute(query_str, variables=None):
        return gql_client.execute(gql(query_str), variable_values=variables or {})
    return _execute
```

---

## Step 4: Test cases per Query

### Happy path
```python
def test_{query_name}_success(execute):
    result = execute("""
        query {
            {queryName}(id: "valid_id") {
                id
                field1
                field2
            }
        }
    """)
    assert result["{queryName}"] is not None
    assert "id" in result["{queryName}"]
```

### Null / not found
```python
def test_{query_name}_not_found(execute):
    result = execute("""
        query {
            {queryName}(id: "nonexistent_99999") {
                id
            }
        }
    """)
    assert result["{queryName}"] is None
```

### Missing required argument
```python
def test_{query_name}_missing_argument(execute):
    with pytest.raises(Exception) as exc_info:
        execute("query { {queryName} { id } }")  # missing required arg
    assert "argument" in str(exc_info.value).lower()
```

---

## Step 5: Test cases per Mutation

### Happy path
```python
def test_{mutation_name}_success(execute):
    result = execute("""
        mutation {
            {mutationName}(input: {field1: "value", field2: 123}) {
                id
                field1
            }
        }
    """)
    assert result["{mutationName}"]["id"] is not None
```

### Invalid input type
```python
def test_{mutation_name}_invalid_input(execute):
    with pytest.raises(Exception) as exc_info:
        execute("""
            mutation {
                {mutationName}(input: {field1: 999}) { id }
            }
        """)
    assert "String" in str(exc_info.value) or "invalid" in str(exc_info.value).lower()
```

### Auth failure
```python
def test_{mutation_name}_unauthenticated():
    transport = RequestsHTTPTransport(url=os.getenv("GRAPHQL_ENDPOINT"))
    client = Client(transport=transport)
    with pytest.raises(Exception) as exc_info:
        client.execute(gql("mutation { {mutationName}(input: {}) { id } }"))
    assert "unauthorized" in str(exc_info.value).lower() or "401" in str(exc_info.value)
```

---

## Step 6: N+1 query detection test

Always generate this — common GraphQL performance issue:

```python
def test_no_n_plus_one_{resource}(execute):
    """Ensure nested queries don't trigger N+1 — use DataLoader pattern."""
    import time
    start = time.time()
    result = execute("""
        query {
            {listQuery}(limit: 50) {
                id
                nested_resource { id name }
            }
        }
    """)
    elapsed = time.time() - start
    assert len(result["{listQuery}"]) == 50
    assert elapsed < 2.0, f"Possible N+1 detected — query took {elapsed:.2f}s"
```

---

## Step 7: Subscriptions

Flag subscription types with a comment — don't generate tests automatically:
```python
# TODO: Subscription {name} requires WebSocket transport
# Use gql AsyncClient with WebsocketsTransport for subscription tests
# Manual test design recommended
```

---

## Output rules

- Separate files for queries vs mutations — never mix
- Extract long query strings to `/queries/*.graphql` files, import via `Path.read_text()`
- All credentials via `os.getenv()`
- Flag custom scalars: `# TODO: custom scalar {name} — add validation logic`
- N+1 test generated for every list query with nested types
