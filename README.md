# AI-Powered Test Framework

An AI-native test automation framework combining **Claude Code subagents** for interactive development and **reusable skill prompts** for programmatic test generation — covering the full testing pyramid across REST, gRPC, and GraphQL APIs.

Built by [Swapnil Tilaye](https://linkedin.com/in/swapniltilaye) — Sr. SDET | GitHub: [github.com/stilaye](https://github.com/stilaye)

---

## Two ways to use this framework

| | Claude Code Agents | Skills (Prompt Templates) |
|---|---|---|
| **Location** | `.claude/agents/` | `skills/` |
| **Who calls it** | Claude Code — invoked automatically based on context | Your code — loaded programmatically as Claude API system prompts |
| **Best for** | Interactive development: writing tests while coding | Autonomous generation: CI/CD pipelines, CLI tools, agentic workflows |
| **Requires** | Claude Code CLI | Anthropic API key |
| **How to trigger** | Describe the task in Claude Code — it picks the right agent | `skill = Path("skills/openapi-pytest-builder.md").read_text()` |

---

## Claude Code Agents (`.claude/agents/`)

Use these when working interactively inside this repo with Claude Code. Claude detects your intent and invokes the right agent automatically.

### Existing agents (project-aware)

| Agent | When Claude invokes it |
|---|---|
| `framework-architect` | "Refactor this framework", "Make this more modular" |
| `pytest-test-developer` | "Write tests for these endpoints", "Review my test coverage" |
| `test-gap-analyzer` | "What am I missing?", "Analyze coverage gaps against this spec" |
| `test-results-analyzer` | "Why are these tests failing?", "Analyze this test run" |

### New agents (API test generation)

| Agent | When Claude invokes it | Color |
|---|---|---|
| `openapi-pytest-builder` | "Generate tests from this openapi.yaml/swagger.json" | Blue |
| `grpc-pytest-builder` | "Write pytest for this .proto file" | Purple |
| `graphql-pytest-builder` | "Generate tests for this GraphQL schema" | Pink |
| `contract-test-builder` | "Write contract tests between service A and B" | Green |
| `perf-test-builder` | "Write load tests for this flow" | Orange |
| `api-security-builder` | "Generate OWASP security tests for this API" | Red |
| `integration-mock-builder` | "Mock this downstream service for integration tests" | Yellow |
| `e2e-flow-builder` | "Write e2e tests for login to checkout to payment" | Cyan |

### How to use agents

```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Clone and open this repo
git clone https://github.com/stilaye/ai-poweredtestframework
cd ai-poweredtestframework
claude  # agents are auto-loaded from .claude/agents/

# Then just describe what you need:
# "Generate pytest tests from docs/openapi.yaml"
# "Write OWASP security tests for the payment API"
# "Create e2e tests for the checkout journey"
```

---

## Skills — Prompt Templates (`skills/`)

Use these when you want programmatic test generation — loaded by your framework, CLI, or CI pipeline as Claude API system prompts.

### Available skills

| Skill file | Spec type | Test type | Key output |
|---|---|---|---|
| `openapi-pytest-builder.md` | OpenAPI YAML/JSON | Functional | pytest suite, live + mock mode |
| `grpc-pytest-builder.md` | `.proto` file | Functional | pytest + gRPC stubs, all status codes |
| `graphql-pytest-builder.md` | GraphQL SDL | Functional | pytest, queries + mutations + N+1 detection |
| `contract-test-builder.md` | Any spec | Contract + Drift | Pact consumer/provider + snapshot mode |
| `perf-test-builder.md` | Any spec + user journey | Performance | Journey-based Locust + 3 load profiles |
| `api-security-builder.md` | Any spec | Security | OWASP API Top 10, gRPC + GraphQL variants |
| `integration-mock-builder.md` | Any spec | Mocking | WireMock + vcrpy + pytest-httpserver |
| `e2e-flow-builder.md` | Multi-spec + user flow | E2E | Chained pytest with FlowState + cleanup |

### How to use skills programmatically

```python
from pathlib import Path
import anthropic

client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var

def generate_tests(spec_content: str, skill_name: str) -> str:
    skill = Path(f"skills/{skill_name}.md").read_text()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        system=skill,
        messages=[{"role": "user", "content": f"Generate tests:\n\n{spec_content}"}]
    )
    return response.content[0].text

# REST / OpenAPI
tests = generate_tests(Path("docs/openapi.yaml").read_text(), "openapi-pytest-builder")

# gRPC
tests = generate_tests(Path("proto/payment.proto").read_text(), "grpc-pytest-builder")

# GraphQL
tests = generate_tests(Path("schema.graphql").read_text(), "graphql-pytest-builder")
```

### E2E flow — multi-spec + user journey

```python
skill = Path("skills/e2e-flow-builder.md").read_text()
response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=6000,
    system=skill,
    messages=[{
        "role": "user",
        "content": """
        Flow: User logs in → searches product → adds to cart → payment charges card

        Services:
        Auth (OpenAPI): <paste auth spec>
        Product (OpenAPI): <paste product spec>
        Payment (gRPC): <paste .proto>
        """
    }]
)
```

### Use in CI/CD (GitHub Actions)

```yaml
name: Generate API Tests
on:
  push:
    paths: ['specs/**']

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generate tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python scripts/generate_tests.py --spec specs/api.yaml --skill openapi-pytest-builder
      - name: Commit generated tests
        run: |
          git add tests/generated/
          git commit -m "chore: regenerate tests from spec" || exit 0
          git push
```

---

## Decision guide — when to use agents vs skills

```
Writing code interactively in Claude Code?
  YES → .claude/agents/ — Claude picks the right agent automatically

Framework or pipeline calling Claude API directly?
  YES → skills/ — load the .md file as a system prompt

Using Claude.ai browser or app?
  YES → Install .skill packages via Settings → Skills
```

---

## Spec type quick reference

```
.yaml / .json  (OpenAPI)  → openapi-pytest-builder
.proto         (gRPC)     → grpc-pytest-builder
.graphql / SDL (GraphQL)  → graphql-pytest-builder

Multi-service user journey → e2e-flow-builder
Contract validation        → contract-test-builder
OWASP security coverage    → api-security-builder
Load / performance tests   → perf-test-builder
Stub downstream services   → integration-mock-builder
```

---

## Full testing pyramid

```
         ┌──────────────────────────┐
         │      E2E / Journey       │  ← e2e-flow-builder
         ├──────────────────────────┤
         │    Contract Testing      │  ← contract-test-builder
         ├──────────────────────────┤
         │  Integration / Mocking   │  ← integration-mock-builder
         ├──────────────────────────┤
         │    Security Testing      │  ← api-security-builder
         ├──────────────────────────┤
         │  Performance Testing     │  ← perf-test-builder
         ├──────────────────────────┤
         │   Functional Testing     │  ← openapi / grpc / graphql builders
         └──────────────────────────┘
```

---

## Project structure

```
ai-poweredtestframework/
├── .claude/
│   └── agents/                         ← Claude Code subagents (interactive)
│       ├── framework-architect.md      ← existing
│       ├── pytest-test-developer.md    ← existing
│       ├── test-gap-analyzer.md        ← existing
│       ├── test-results-analyzer.md    ← existing
│       ├── openapi-pytest-builder.md   ← new
│       ├── grpc-pytest-builder.md      ← new
│       ├── graphql-pytest-builder.md   ← new
│       ├── contract-test-builder.md    ← new
│       ├── perf-test-builder.md        ← new
│       ├── api-security-builder.md     ← new
│       ├── integration-mock-builder.md ← new
│       └── e2e-flow-builder.md         ← new
│
├── skills/                             ← Prompt templates (programmatic)
│   ├── openapi-pytest-builder.md
│   ├── grpc-pytest-builder.md
│   ├── graphql-pytest-builder.md
│   ├── contract-test-builder.md
│   ├── perf-test-builder.md
│   ├── api-security-builder.md
│   ├── integration-mock-builder.md
│   └── e2e-flow-builder.md
│
├── docs/
├── examples/
└── README.md
```

---

## Requirements

```bash
pip install pytest requests httpx grpcio grpcio-tools gql \
            pact-python responses respx locust bandit \
            jsonschema vcrpy pytest-httpserver anthropic
```

---

## Author

**Swapnil Tilaye** — Senior QA/SDET | 12+ years | San Jose, CA

Key projects: DeCAF (Python BLE framework) · BLINK (ESP32 benchmarking) · KIRO (MCP agentic workspace) · SmartTestGen (AI test generation)

- GitHub: [github.com/stilaye](https://github.com/stilaye)
- LinkedIn: [linkedin.com/in/swapniltilaye](https://linkedin.com/in/swapniltilaye)
