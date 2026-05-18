# specs/

Drop your API spec files here. Skills auto-detect the format.

| File type | Format | Skill that uses it |
|---|---|---|
| `*.yaml` / `*.json` | OpenAPI / Swagger | openapi-pytest-builder |
| `*.proto` | gRPC Protocol Buffers | grpc-pytest-builder |
| `*.graphql` / `*.gql` | GraphQL SDL | graphql-pytest-builder |
| Any of the above | Multiple services | e2e-flow-builder, contract-test-builder |

## Naming convention

```
specs/
  auth.yaml              ← OpenAPI spec for auth service
  payment.proto          ← gRPC spec for payment service
  product.graphql        ← GraphQL schema for product service
  user.yaml              ← OpenAPI spec for user service
```

## How skills find your spec

1. **Auto-detect** — if one spec file exists, skills use it automatically
2. **You specify** — "use specs/payment.proto" in your prompt
3. **Multiple specs** — skill asks which one if ambiguous
4. **No spec** — skill asks: "Paste your spec, provide a path, or give a URL"
