# CLAUDE.md

This file is read by Claude Code at session start. It tells Claude how this repo is structured and how to behave when working in it.

---

## What this repo is

An AI-powered test framework for generating pytest test suites across REST, gRPC, and GraphQL APIs. It uses Claude Code skills for domain expertise and subagents for active specialist tasks.

---

## Project conventions

### Spec files live in `specs/`
All API spec files go in `specs/`. Claude should always check here first before asking the user for a spec.

```
specs/
  *.yaml / *.json   → OpenAPI / Swagger specs
  *.proto           → gRPC Protocol Buffer definitions
  *.graphql / *.gql → GraphQL SDL schemas
```

### Generated tests go in `tests/generated/`
Never overwrite files in `tests/` directly. Always write generated output to `tests/generated/`.

### Skills are in `.claude/skills/`
8 test generation skills — Claude loads the relevant one based on task context. See `.claude/skills/` for available skills.

### Agents are in `.claude/agents/`
4 active specialist agents for framework work. Claude spawns these when doing active analysis or refactoring tasks.

---

## How to behave

### On specs
- Always check `specs/` first before asking the user for a spec
- If one spec file exists → use it automatically
- If multiple exist → ask once: "Which spec? (list them)"
- If none exist → ask once: "Paste your spec, give a path, or provide a URL"

### On test generation
- Default output: `tests/generated/`
- Default mode: live endpoint (not mock) unless user says otherwise
- Default language: Python / pytest
- Never ask more than one clarifying question before starting

### On framework changes
- Use `framework-architect` agent for structural refactoring
- Use `test-gap-analyzer` agent for coverage analysis
- Never modify existing tests in `tests/` — always create new files

### On committing
- Never commit generated test files unless user explicitly asks
- Always use conventional commits: `feat:`, `fix:`, `chore:`, `test:`

---

## Skills quick reference

| Say this... | Skill that loads |
|---|---|
| "Generate tests from openapi.yaml" | openapi-pytest-builder |
| "Write pytest for this .proto file" | grpc-pytest-builder |
| "Test this GraphQL schema" | graphql-pytest-builder |
| "Write contract tests" | contract-test-builder |
| "Load test this flow" | perf-test-builder |
| "OWASP security tests" | api-security-builder |
| "Mock this downstream service" | integration-mock-builder |
| "E2E tests for this user journey" | e2e-flow-builder |

---

## Agents quick reference

| Say this... | Agent that runs |
|---|---|
| "Refactor the framework" | framework-architect |
| "Write tests for these endpoints" | pytest-test-developer |
| "What test coverage am I missing?" | test-gap-analyzer |
| "Why are these tests failing?" | test-results-analyzer |
