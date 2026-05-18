---
name: grpc-pytest-builder
description: "Use this agent when given a gRPC Protocol Buffer (.proto) file and asked to generate pytest tests. Examples: <example>Context: User has a .proto file. user: 'Write pytest tests for this proto file' assistant: 'I will use the grpc-pytest-builder agent to generate a pytest suite with stub compilation and gRPC status code coverage.' <commentary>Proto file input — invoke grpc-pytest-builder.</commentary></example>"
color: purple
---


# gRPC Pytest Builder Skill

## Who this is for
Swapnil Tilaye — Python-first SDET. gRPC background from EdgeQ 5G platform work.
Libraries: `grpcio`, `grpcio-testing`, `pytest`, `grpcio-tools` for stub generation.

---

## Step 1: Parse the .proto file

Extract:
- Package name
- Service name(s) and RPC methods
- Request/response message types per method
- Field names, types, required vs optional
- Streaming type: unary, server-streaming, client-streaming, bidirectional

---

## Step 2: Generate stub compilation command

Always output this first so user can generate Python stubs:

```bash
python -m grpc_tools.protoc \
  -I. \
  --python_out=. \
  --grpc_python_out=. \
  your_service.proto
```

This generates:
- `your_service_pb2.py` — message classes
- `your_service_pb2_grpc.py` — stub and servicer classes

---

## Step 3: File structure

```
tests/
  conftest.py                  → channel fixture, stub fixture, shared setup
  test_{service_name}.py       → one file per gRPC service
```

---

## Step 4: conftest.py structure

```python
import pytest
import grpc
from your_service_pb2_grpc import YourServiceStub

@pytest.fixture(scope="session")
def grpc_channel():
    channel = grpc.insecure_channel("localhost:50051")
    yield channel
    channel.close()

@pytest.fixture(scope="session")
def stub(grpc_channel):
    return YourServiceStub(grpc_channel)

@pytest.fixture
def metadata():
    # Auth metadata — replace with env var in CI
    return [("authorization", f"Bearer {os.getenv('GRPC_TOKEN', '')}")]
```

---

## Step 5: Test cases per RPC method

### Unary RPC — happy path
```python
def test_{method_name}_success(stub, metadata):
    request = YourRequest(field1="value", field2=123)
    response = stub.YourMethod(request, metadata=metadata)
    assert response.status == "OK"
    assert response.field is not None
```

### Invalid request — missing required fields
```python
def test_{method_name}_empty_request(stub, metadata):
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.YourMethod(YourRequest(), metadata=metadata)
    assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT
```

### Auth failure
```python
def test_{method_name}_unauthenticated(stub):
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.YourMethod(valid_request, metadata=[])
    assert exc_info.value.code() == grpc.StatusCode.UNAUTHENTICATED
```

### Not found
```python
def test_{method_name}_not_found(stub, metadata):
    request = YourRequest(id="nonexistent_99999")
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.YourMethod(request, metadata=metadata)
    assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND
```

### Server streaming RPC
```python
def test_{method_name}_streaming(stub, metadata):
    request = YourStreamRequest(param="value")
    responses = list(stub.YourStreamMethod(request, metadata=metadata))
    assert len(responses) > 0
    for r in responses:
        assert r.field is not None
```

### Deadline / timeout
```python
def test_{method_name}_deadline_exceeded(stub, metadata):
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.YourMethod(valid_request, metadata=metadata, timeout=0.001)
    assert exc_info.value.code() == grpc.StatusCode.DEADLINE_EXCEEDED
```

---

## Step 6: gRPC status codes to cover

Always generate tests for these where applicable:
- `OK` — happy path
- `INVALID_ARGUMENT` — bad request fields
- `NOT_FOUND` — resource doesn't exist
- `UNAUTHENTICATED` — missing/invalid token
- `PERMISSION_DENIED` — valid token, wrong scope
- `DEADLINE_EXCEEDED` — timeout test
- `UNAVAILABLE` — server down (use mock channel for this)

---

## Step 7: Mock mode

Use `grpc_testing` for in-process mocking without a live server:

```python
import grpc_testing

def test_{method_name}_mocked():
    servicer = MockYourServiceServicer()
    server = grpc_testing.server_from_dictionary(
        {your_service_pb2.DESCRIPTOR.services_by_name['YourService']: servicer},
        grpc_testing.strict_real_time()
    )
    # invoke and assert against mock servicer
```

---

## Output rules

- Always output stub compilation command before test files
- One test file per gRPC service definition
- Use `grpc.StatusCode` enums — never raw integer codes
- All credentials via `os.getenv()` — no hardcoded tokens
- Flag bidirectional streaming methods with comment: `# TODO: bidirectional streaming — manual test design recommended`
