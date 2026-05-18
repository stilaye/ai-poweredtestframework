---
name: openapi-pytest-builder
description: "Use this agent when given an OpenAPI/Swagger spec (YAML or JSON) and asked to generate a pytest test suite. Examples: <example>Context: User has an OpenAPI spec file. user: 'Generate pytest tests from this openapi.yaml' assistant: 'I will use the openapi-pytest-builder agent to generate a full pytest suite with happy path, auth, and negative tests.' <commentary>User has a spec and needs test generation — invoke openapi-pytest-builder.</commentary></example> <example>Context: No live endpoint available. user: 'Write tests for this API but I dont have a live server yet' assistant: 'I will use the openapi-pytest-builder agent in mock mode using the responses library.' <commentary>No live endpoint — agent generates mock variant.</commentary></example>"
color: blue
---

$(cat /home/claude/api-skills/openapi-pytest-builder/SKILL.md | sed '/^---$/,/^---$/d' | tail -n +2)
