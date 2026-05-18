---
name: e2e-flow-builder
description: >
  Generate end-to-end functional test suites from user flow descriptions that span
  multiple services. Trigger for "write e2e tests", "end to end test for this flow",
  "test this user journey", "multi-service test", "integration flow test",
  "test across services", or when given a flow description involving more than one
  service/API. Accepts plain English flow description + service map (OpenAPI/proto/GraphQL).
  Generates chained pytest tests with shared state management and cleanup.
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


# E2E Flow Builder Skill

## Who this is for
Swapnil Tilaye — Python-first SDET. Multi-service testing background from F5 Networks
(microservices, distributed systems), EdgeQ (5G stack, CU/DU/Core), Mimic (agentic pipelines).
Libraries: `pytest`, `requests`, `grpcio`, `gql` — mixed as needed per service type.

---

## Step 1: Gather inputs (both required)

### Input 1 — User flow (plain English)
Accept voice-dump style, fragmented, or structured. Examples:

> "User logs in, searches product, adds to cart, checks out, payment charges card,
>  notification sends email confirmation"

> "Device registers via BLE, firmware validates pairing, cloud syncs device state,
>  dashboard reflects status"

Parse into ordered steps — each step = one service interaction.

### Input 2 — Service map
For each service involved, ask:
- Service name
- Spec type (OpenAPI / gRPC .proto / GraphQL / REST no-spec)
- Base URL or endpoint
- Auth mechanism

If spec files are provided, parse them using the relevant spec skill patterns
(openapi-pytest-builder / grpc-pytest-builder / graphql-pytest-builder).

---

## Step 2: Build the flow graph

Before writing any code, output a flow diagram as a comment block:

```python
"""
E2E Flow: {Flow Name}
======================
Step 1: [Auth Service]        POST /auth/login
           ↓ token
Step 2: [Product Service]     GET /products/search
           ↓ product_id
Step 3: [Cart Service]        POST /cart/add
           ↓ cart_id
Step 4: [Payment Service]     gRPC ChargeCard(cart_id, amount)
           ↓ payment_id
Step 5: [Notification Service] GET /notifications/{cart_id}
           ↓ assert email_sent=True

Shared state: token → product_id → cart_id → payment_id
Cleanup: DELETE /cart/{cart_id}, DELETE /orders/{order_id}
"""
```

This makes the test self-documenting and interview-ready.

---

## Step 3: File structure

```
tests/
  e2e/
    test_{flow_name}.py          → main journey test(s)
    test_{flow_name}_negative.py → failure path scenarios
    conftest_e2e.py              → all service clients, shared state, cleanup
    fixtures/
      test_data.py               → reusable data factories
      service_clients.py         → one client class per service
```

---

## Step 4: Shared state pattern (core of this skill)

Use a `FlowState` dataclass to pass state between steps — never use global variables:

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class FlowState:
    """Carries state across all steps of the {flow_name} journey."""
    # Populated progressively as flow executes
    token: Optional[str] = None
    user_id: Optional[str] = None
    product_id: Optional[str] = None
    cart_id: Optional[str] = None
    payment_id: Optional[str] = None
    order_id: Optional[str] = None
    # Add fields per flow
    created_resources: list = field(default_factory=list)  # for cleanup
```

---

## Step 5: conftest_e2e.py

```python
import pytest
import requests
import os
from .fixtures.service_clients import (
    AuthServiceClient,
    ProductServiceClient,
    PaymentServiceStub,   # gRPC
    NotificationClient
)
from .test_data import FlowState

@pytest.fixture(scope="module")
def flow_state():
    """Shared state object for entire flow — scoped to module."""
    return FlowState()

@pytest.fixture(scope="module")
def auth_client():
    return AuthServiceClient(base_url=os.getenv("AUTH_SERVICE_URL"))

@pytest.fixture(scope="module")
def product_client():
    return ProductServiceClient(base_url=os.getenv("PRODUCT_SERVICE_URL"))

@pytest.fixture(scope="module")
def payment_stub():
    import grpc
    from payment_pb2_grpc import PaymentServiceStub
    channel = grpc.insecure_channel(os.getenv("PAYMENT_GRPC_URL", "localhost:50051"))
    return PaymentServiceStub(channel)

@pytest.fixture(scope="module", autouse=True)
def cleanup(flow_state, auth_client):
    """Auto-cleanup after all tests in module complete."""
    yield
    for resource in reversed(flow_state.created_resources):
        try:
            requests.delete(
                resource["url"],
                headers={"Authorization": f"Bearer {flow_state.token}"}
            )
        except Exception as e:
            print(f"Cleanup warning: {e}")
```

---

## Step 5b: Multi-spec client fixtures

When a flow spans different spec types, generate the right client fixture per service:

### gRPC service fixture
```python
@pytest.fixture(scope="module")
def {service_name}_stub():
    import grpc
    from {service}_pb2_grpc import {ServiceName}Stub
    channel = grpc.insecure_channel(
        os.getenv("{SERVICE_NAME}_GRPC_URL", "localhost:50051")
    )
    stub = {ServiceName}Stub(channel)
    yield stub
    channel.close()

# gRPC metadata helper (auth)
@pytest.fixture(scope="module")
def grpc_metadata(flow_state):
    """Returns after token is populated in step 1."""
    def _metadata():
        return [("authorization", f"Bearer {flow_state.token}")]
    return _metadata
```

### GraphQL service fixture
```python
@pytest.fixture(scope="module")
def {service_name}_gql():
    from gql import Client, gql
    from gql.transport.requests import RequestsHTTPTransport
    transport = RequestsHTTPTransport(
        url=os.getenv("{SERVICE_NAME}_GRAPHQL_URL"),
        headers={"Authorization": f"Bearer {os.getenv('GQL_TOKEN', '')}"}
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)
    yield client

# GraphQL execute helper with dynamic auth
def make_gql_execute(client, flow_state):
    from gql import gql
    def _execute(query_str, variables=None):
        # Inject token into transport headers dynamically
        client.transport.headers["Authorization"] = f"Bearer {flow_state.token}"
        return client.execute(gql(query_str), variable_values=variables or {})
    return _execute
```

### REST service fixture
```python
@pytest.fixture(scope="module")
def {service_name}_client():
    session = requests.Session()
    session.base_url = os.getenv("{SERVICE_NAME}_URL")
    yield session
    session.close()
```

### Mixed flow step examples

```python
# gRPC step
def test_step_0N_grpc_call(self, flow_state, {service}_stub, grpc_metadata):
    from {service}_pb2 import {RequestType}
    response = {service}_stub.{MethodName}(
        {RequestType}(id=flow_state.resource_id),
        metadata=grpc_metadata()
    )
    assert response.status == "OK"
    flow_state.result_id = response.result_id

# GraphQL step
def test_step_0N_graphql_query(self, flow_state, {service}_gql):
    execute = make_gql_execute({service}_gql, flow_state)
    result = execute("""
        query GetResource($id: ID!) {
            resource(id: $id) { id status details }
        }
    """, variables={"id": flow_state.resource_id})
    assert result["resource"]["status"] == "active"
    flow_state.details = result["resource"]["details"]
```

---

## Step 6: service_clients.py pattern

One thin client class per service — wraps HTTP calls with auth:

```python
class {ServiceName}Client:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    def _headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def {method_name}(self, payload: dict, token: str) -> dict:
        response = self.session.post(
            f"{self.base_url}/endpoint",
            json=payload,
            headers=self._headers(token)
        )
        response.raise_for_status()
        return response.json()
```

---

## Step 7: Main flow test — happy path

Use `pytest` ordering with `pytest-ordering` or sequential function names to enforce step order:

```python
import pytest

class Test{FlowName}HappyPath:
    """
    E2E: {Flow description}
    Tests run sequentially — each step depends on previous state.
    """

    def test_step_01_authenticate(self, flow_state, auth_client):
        """Step 1: User authenticates and receives token."""
        result = auth_client.login({
            "username": os.getenv("E2E_TEST_USER"),
            "password": os.getenv("E2E_TEST_PASS")
        })
        assert result.get("access_token"), "Login failed — no token returned"
        flow_state.token = result["access_token"]
        flow_state.user_id = result.get("user_id")

    def test_step_02_search_product(self, flow_state, product_client):
        """Step 2: User searches for a product."""
        assert flow_state.token, "Skipping — Step 1 failed"
        result = product_client.search("test product", flow_state.token)
        assert len(result["items"]) > 0, "No products returned"
        flow_state.product_id = result["items"][0]["id"]

    def test_step_03_add_to_cart(self, flow_state, product_client):
        """Step 3: User adds product to cart."""
        assert flow_state.product_id, "Skipping — Step 2 failed"
        result = product_client.add_to_cart(flow_state.product_id, flow_state.token)
        assert result["cart_id"], "Cart creation failed"
        flow_state.cart_id = result["cart_id"]
        flow_state.created_resources.append({
            "url": f"{os.getenv('PRODUCT_SERVICE_URL')}/cart/{result['cart_id']}"
        })

    def test_step_04_payment(self, flow_state, payment_stub):
        """Step 4: Payment service charges card (gRPC)."""
        assert flow_state.cart_id, "Skipping — Step 3 failed"
        from payment_pb2 import ChargeRequest
        response = payment_stub.ChargeCard(
            ChargeRequest(
                cart_id=flow_state.cart_id,
                amount=99.99,
                currency="USD"
            ),
            metadata=[("authorization", f"Bearer {flow_state.token}")]
        )
        assert response.status == "SUCCESS"
        flow_state.payment_id = response.payment_id

    def test_step_05_notification(self, flow_state, notification_client):
        """Step 5: Notification service sends confirmation."""
        assert flow_state.payment_id, "Skipping — Step 4 failed"
        result = notification_client.get_confirmation(
            flow_state.cart_id, flow_state.token
        )
        assert result["email_sent"] is True
        assert result["recipient"] == os.getenv("E2E_TEST_USER")
```

---

## Step 8: Negative flow tests

Generate failure scenarios for critical steps only — not every step:

```python
class Test{FlowName}NegativePaths:

    def test_payment_failure_rolls_back_cart(
        self, flow_state, product_client, payment_stub
    ):
        """If payment fails, cart should be restored to pre-checkout state."""
        # Setup: get to checkout step
        cart = product_client.add_to_cart("test_product_id", flow_state.token)

        # Force payment failure
        from payment_pb2 import ChargeRequest
        with pytest.raises(grpc.RpcError) as exc:
            payment_stub.ChargeCard(
                ChargeRequest(cart_id=cart["cart_id"], amount=-1.00)
            )
        assert exc.value.code() == grpc.StatusCode.INVALID_ARGUMENT

        # Verify cart still exists (rollback worked)
        cart_status = product_client.get_cart(cart["cart_id"], flow_state.token)
        assert cart_status["status"] == "active", "Cart not rolled back after payment failure"

    def test_expired_token_mid_flow(self, product_client):
        """Flow should fail gracefully with expired token."""
        expired_token = os.getenv("E2E_EXPIRED_TOKEN", "expired.token.here")
        with pytest.raises(requests.HTTPError) as exc:
            product_client.search("anything", expired_token)
        assert exc.value.response.status_code == 401
```

---

## Step 9: test_data.py factories

```python
import uuid

def make_test_user(suffix=None):
    """Generate unique test user to avoid conflicts between parallel runs."""
    uid = suffix or str(uuid.uuid4())[:8]
    return {
        "username": f"e2e_test_user_{uid}@test.com",
        "password": "E2eTestP@ss123!"
    }

def make_test_product():
    return {
        "name": f"E2E Test Product {uuid.uuid4().hex[:6]}",
        "price": 99.99,
        "sku": f"E2E-{uuid.uuid4().hex[:8].upper()}"
    }
```

---

## Output rules

- Always generate the flow diagram comment block at top of test file
- `FlowState` dataclass is mandatory — never use module-level variables for state
- Each test step checks previous state with `assert flow_state.{field}, "Skipping — Step N failed"` — prevents cascading failures with misleading errors
- Cleanup fixture always uses `reversed(created_resources)` — delete in reverse creation order
- All URLs and credentials via `os.getenv()`
- Negative tests only for steps with meaningful rollback behavior — not every step
- Use `scope="module"` for all service client fixtures — don't recreate per test
- **Multi-spec flows:** generate correct fixture type per service (REST session / gRPC stub / GraphQL gql Client) — never use requests for gRPC or GraphQL steps
- **gRPC auth:** always use `grpc_metadata()` callable fixture — not hardcoded metadata — so token updates propagate after step 1
- **GraphQL auth:** always use `make_gql_execute()` helper to inject live token into transport headers dynamically
- Flag async flows (webhooks, event-driven): `# TODO: add polling or webhook listener for async step`
- Generate `.env.example` file listing all required env vars for the flow
