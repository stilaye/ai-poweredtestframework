---
name: perf-test-builder
description: >
  Generate Locust-based performance test files modeled on user journeys, not individual
  endpoints. Trigger for "write performance tests", "load test this API", "generate Locust",
  "stress test", "benchmark this API", "perf tests". Requires both a spec (OpenAPI/proto/
  GraphQL) AND a description of key user journeys. Always defaults to Locust (Python).
  Generates JMeter .jmx only if explicitly requested.
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


# Perf Test Builder Skill

## Who this is for
Swapnil Tilaye — Python-first SDET. Locust experience from F5 Networks.
Default tool: **Locust**. JMeter only on explicit request.

---

## Step 1: Gather inputs (both required)

1. **API spec** — OpenAPI / .proto / GraphQL schema
2. **User journeys** — ask if not provided:
   > "What are the 2–3 main things a real user does in this system? e.g. 'login → search → view item → checkout'"

Do NOT generate per-endpoint tests. Model realistic user behavior flows only.

---

## Step 2: Determine journey weights

Ask or infer from context:
> "Which journey happens most often in production?"

Default weight ratios if not specified:
- Read/browse journeys: weight 5–7
- Search/filter: weight 3–4
- Write/create: weight 2
- Delete/admin: weight 1

---

## Step 3: File structure

```
perf/
  locustfile.py              → main entry point, all TaskSets
  load_profiles/
    smoke.py                 → 5 users, 1 min, verify baseline
    load.py                  → 100 users, ramp 10/sec, 10 min
    stress.py                → spike to 500 users, find breaking point
  conftest_perf.py           → shared fixtures (auth, base URL)
```

---

## Step 4: locustfile.py structure

```python
from locust import HttpUser, TaskSet, task, between
import os

class {JourneyName}Tasks(TaskSet):
    """
    Models: {description of journey}
    Weight ratios reflect production traffic patterns.
    """

    def on_start(self):
        """Auth flow — runs once per simulated user."""
        response = self.client.post("/auth/login", json={
            "username": os.getenv("PERF_USER", "testuser"),
            "password": os.getenv("PERF_PASS", "testpass")
        })
        self.token = response.json().get("access_token", "")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(5)  # highest weight = most common action
    def {most_common_action}(self):
        with self.client.get(
            "/endpoint",
            headers=self.headers,
            name="/endpoint [description]",  # name groups requests in Locust UI
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Expected 200, got {response.status_code}")
            elif response.elapsed.total_seconds() > 2.0:
                response.failure("Response too slow > 2s")

    @task(2)
    def {write_action}(self):
        payload = {"field1": "perf_test_value", "field2": 123}
        with self.client.post(
            "/endpoint",
            json=payload,
            headers=self.headers,
            name="/endpoint [write]",
            catch_response=True
        ) as response:
            if response.status_code not in [200, 201]:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(1)
    def {cleanup_action}(self):
        pass  # lowest frequency action


class {AppName}User(HttpUser):
    host = os.getenv("PERF_BASE_URL", "http://localhost:8080")
    wait_time = between(1, 3)  # think time between tasks
    tasks = [{JourneyName}Tasks]
```

---

## Step 5: Load profiles

### smoke.py — sanity check, not a load test
```python
# locust -f locustfile.py --users 5 --spawn-rate 1 --run-time 1m --headless
# Purpose: verify baseline — no errors at minimal load
# Pass criteria: 0% error rate, p95 < 500ms
```

### load.py — realistic production load
```python
# locust -f locustfile.py --users 100 --spawn-rate 10 --run-time 10m --headless
# Purpose: sustained load at expected production volume
# Pass criteria: error rate < 1%, p95 < 1s, p99 < 2s
```

### stress.py — find the breaking point
```python
# locust -f locustfile.py --users 500 --spawn-rate 50 --run-time 5m --headless
# Purpose: spike load, observe degradation pattern
# Pass criteria: system recovers after spike, no data corruption
```

---

## Step 6: Response time thresholds (encode in tests)

| Endpoint type | p95 target | p99 target |
|---|---|---|
| Read / GET | < 500ms | < 1s |
| Write / POST | < 1s | < 2s |
| Search / filter | < 1s | < 2s |
| Auth / login | < 500ms | < 1s |
| Heavy compute | < 3s | < 5s |

Use `catch_response=True` + `response.failure()` to flag SLA breaches in Locust UI.

---

## Step 7: JMeter fallback (only if explicitly requested)

Generate a basic `.jmx` test plan with:
- Thread Group per journey
- HTTP Request samplers per step
- Response Assertion (status code)
- Summary Report listener

Note to user:
```
# JMeter .jmx generated as requested.
# Recommended: use Locust for Python-native CI/CD pipelines.
# JMeter requires headless mode (jmeter -n -t test.jmx) for CI integration.
```

---

## Output rules

- Never generate per-endpoint TaskSets — journeys only
- Always use `name=` parameter in Locust requests for clean UI grouping
- Always use `catch_response=True` with explicit failure conditions
- All credentials and URLs via `os.getenv()`
- Include pass/fail criteria as comments in each load profile
- Flag any endpoint requiring OAuth2 flow with: `# TODO: implement OAuth2 PKCE flow in on_start`
