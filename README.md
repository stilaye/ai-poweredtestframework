# AI-Powered Test Framework

An AI-native test automation framework using **Claude Code skills** for domain expertise and **subagents** for parallel execution — covering the full testing pyramid across REST, gRPC, and GraphQL APIs.

Built by [Swapnil Tilaye](https://linkedin.com/in/swapniltilaye) — Sr. SDET | [github.com/stilaye](https://github.com/stilaye)

---

## `.claude/` folder — quick reference

```
.claude/
  agents/    ← Subagents: isolated workers spawned for specialist tasks
  skills/    ← Skills: domain expertise injected into current context
  commands/  ← Slash commands: /deploy, /test, /review etc
  rules/     ← Scoped rules applied by file path or context
  hooks/     ← Event hooks: run logic on session start, file save etc
```

---

## Agents vs Skills — know the difference

| | Agents (`.claude/agents/`) | Skills (`.claude/skills/`) |
|---|---|---|
| **What** | Specialist subagent with its own isolated context | Reusable instruction set injected into current context |
| **Format** | Single `.md` file | Directory with `SKILL.md` + optional scripts/assets |
| **Context** | Runs isolated — compresses findings, returns to main session | Runs inline — same session, no isolation |
| **Invoked by** | Claude spawns it as a parallel worker | Claude loads it on demand when relevant |
| **Tool access** | Restricted — you define which tools it can use | Inherits current session tools |
| **Best for** | "Do this task for me" — active work | "Know how to do this" — domain expertise |
| **Example** | `framework-architect` refactors your code | `openapi-pytest-builder` knows how to generate tests |

**One-liner:** Agents *do* work. Skills *know* how to do work.

### When to use which

```
Need Claude to actively perform a task in isolation?
  → Agent  (e.g. "review my PR", "analyze test gaps")

Need Claude to apply domain expertise to what you're already doing?
  → Skill  (e.g. "generate tests from this spec", "write security tests")

Need a repeatable slash command workflow?
  → Command  (e.g. /generate-tests, /security-scan)

Need to enforce rules on specific file types or paths?
  → Rule

Need to trigger logic on events (session start, file change)?
  → Hook
```

---

## Agents (`.claude/agents/`)

Active specialist workers. Claude spawns these in isolated context when you need focused, parallel execution.

| Agent | What it does |
|---|---|
| `framework-architect` | Refactors and improves the test framework structure |
| `pytest-test-developer` | Writes pytest test cases from OpenAPI specs |
| `test-gap-analyzer` | Analyzes coverage gaps against specs and requirements |
| `test-results-analyzer` | Diagnoses failing tests and flakiness patterns |

---

## Skills (`.claude/skills/`)

Domain expertise Claude loads automatically when relevant. Each skill is a directory containing a `SKILL.md` file.

| Skill | Spec input | Test type | Key output |
|---|---|---|---|
| `openapi-pytest-builder` | OpenAPI YAML/JSON | Functional | pytest suite, live + mock mode |
| `grpc-pytest-builder` | `.proto` file | Functional | pytest + gRPC stubs, all status codes |
| `graphql-pytest-builder` | GraphQL SDL | Functional | pytest, queries + mutations + N+1 detection |
| `contract-test-builder` | Any spec | Contract + Drift | Pact consumer/provider + snapshot mode |
| `perf-test-builder` | Any spec + user journey | Performance | Journey-based Locust + 3 load profiles |
| `api-security-builder` | Any spec | Security | OWASP API Top 10, REST + gRPC + GraphQL |
| `integration-mock-builder` | Any spec | Mocking | WireMock + vcrpy + pytest-httpserver |
| `e2e-flow-builder` | Multi-spec + user flow | E2E | Chained pytest with FlowState + cleanup |

### How skills are triggered in Claude Code

```bash
claude  # open Claude Code in this repo — skills auto-load

# Then just describe what you need:
"Generate pytest tests from this openapi.yaml"
"Write OWASP security tests for the payment API"
"Create e2e tests for login → checkout → payment flow"
"Write load tests for the checkout journey"
```

---

## Skills as prompt templates (`skills/`)

The same skill files also live in the top-level `skills/` folder for **programmatic use** — loaded by your framework or CI pipeline as Claude API system prompts.

```python
from pathlib import Path
import anthropic

client = anthropic.Anthropic()  # ANTHROPIC_API_KEY env var

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

### CI/CD (GitHub Actions)

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
        run: |
          python scripts/generate_tests.py \
            --spec specs/api.yaml \
            --skill skills/openapi-pytest-builder.md \
            --output tests/generated/
      - name: Commit generated tests
        run: |
          git add tests/generated/
          git commit -m "chore: regenerate tests from spec" || exit 0
          git push
```

---

## Spec type → skill mapping

```
.yaml / .json  (OpenAPI)  →  openapi-pytest-builder
.proto         (gRPC)     →  grpc-pytest-builder
.graphql / SDL (GraphQL)  →  graphql-pytest-builder

Multi-service user journey  →  e2e-flow-builder
Contract validation         →  contract-test-builder
OWASP security coverage     →  api-security-builder
Load / performance tests    →  perf-test-builder
Stub downstream services    →  integration-mock-builder
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
│
├── .claude/
│   ├── agents/                         ← Subagents (isolated workers)
│   │   ├── framework-architect.md
│   │   ├── pytest-test-developer.md
│   │   ├── test-gap-analyzer.md
│   │   └── test-results-analyzer.md
│   │
│   ├── skills/                         ← Skills (domain expertise, auto-loaded)
│   │   ├── openapi-pytest-builder/
│   │   │   └── SKILL.md
│   │   ├── grpc-pytest-builder/
│   │   │   └── SKILL.md
│   │   ├── graphql-pytest-builder/
│   │   │   └── SKILL.md
│   │   ├── contract-test-builder/
│   │   │   └── SKILL.md
│   │   ├── perf-test-builder/
│   │   │   └── SKILL.md
│   │   ├── api-security-builder/
│   │   │   └── SKILL.md
│   │   ├── integration-mock-builder/
│   │   │   └── SKILL.md
│   │   └── e2e-flow-builder/
│   │       └── SKILL.md
│   │
│   ├── commands/                       ← Slash commands (e.g. /generate-tests)
│   ├── rules/                          ← Scoped rules by file path or context
│   └── hooks/                          ← Event hooks (session start, file save)
│
├── skills/                             ← Same skills as flat .md files for
│   ├── openapi-pytest-builder.md         programmatic use via Claude API
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
