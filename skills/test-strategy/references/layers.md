# Test Layers — Detailed Implementation Guide

## Layer 0: Static Analysis

### Per-Language Setup

**Go:**
```yaml
# .golangci.yml
linters:
  enable: [errcheck, govet, staticcheck, unused, ineffassign, gosimple, nilnil, nilerr, bodyclose, sqlclosecheck]
linters-settings:
  errcheck:
    check-blank: true
```

**Python:**
```toml
# pyproject.toml
[tool.ruff]
select = ["E", "F", "W", "I", "N", "S", "B", "A", "C4", "PT", "RET", "SIM"]

[tool.mypy]
strict = true
```

**Rust:**
```toml
# clippy.toml / Cargo.toml
[lints.clippy]
pedantic = "warn"
unwrap_used = "deny"
expect_used = "warn"
```

**TypeScript:**
```json
// .eslintrc or eslint.config.js
{ "extends": ["eslint:recommended", "plugin:@typescript-eslint/strict"] }
// tsconfig.json: "strict": true, "noUncheckedIndexedAccess": true
```

### Pre-commit hook (universal)

```bash
#!/bin/sh
# .git/hooks/pre-commit — detect language and run appropriate linter
if ls *.go &>/dev/null || ls **/*.go &>/dev/null; then golangci-lint run --fix; fi
if [ -f pyproject.toml ] || [ -f setup.py ]; then ruff check --fix . && mypy .; fi
if [ -f Cargo.toml ]; then cargo clippy -- -D warnings; fi
if [ -f package.json ]; then npx eslint . && npx tsc --noEmit; fi
```

---

## Layer 1: Unit Tests

### Table-Driven / Parametrized Tests

**Go:**
```go
func TestParseAmount(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    int64
        wantErr bool
    }{
        {"valid", "100", 100, false},
        {"zero", "0", 0, false},
        {"negative", "-1", 0, true},
        {"empty", "", 0, true},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParseAmount(tt.input)
            if tt.wantErr { require.Error(t, err); return }
            require.NoError(t, err)
            assert.Equal(t, tt.want, got)
        })
    }
}
```

**Python:**
```python
import pytest

@pytest.mark.parametrize("input,expected,raises", [
    ("100", 100, False),
    ("0", 0, False),
    ("-1", None, True),
    ("", None, True),
])
def test_parse_amount(input, expected, raises):
    if raises:
        with pytest.raises(ValueError):
            parse_amount(input)
    else:
        assert parse_amount(input) == expected
```

**Rust:**
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use rstest::rstest;

    #[rstest]
    #[case("100", Ok(100))]
    #[case("0", Ok(0))]
    #[case("-1", Err(_))]
    #[case("", Err(_))]
    fn test_parse_amount(#[case] input: &str, #[case] expected: Result<i64, _>) {
        let result = parse_amount(input);
        assert_eq!(result.is_ok(), expected.is_ok());
        if let Ok(v) = result { assert_eq!(v, expected.unwrap()); }
    }
}
```

**TypeScript:**
```typescript
describe('parseAmount', () => {
  it.each([
    ['100', 100],
    ['0', 0],
  ])('parses %s to %i', (input, expected) => {
    expect(parseAmount(input)).toBe(expected);
  });

  it.each(['-1', ''])('rejects %s', (input) => {
    expect(() => parseAmount(input)).toThrow();
  });
});
```

### Property-Based Tests

**Go** (rapid):
```go
rapid.Check(t, func(t *rapid.T) {
    original := rapid.SliceOf(rapid.Byte()).Draw(t, "data")
    encoded := base64.StdEncoding.EncodeToString(original)
    decoded, err := base64.StdEncoding.DecodeString(encoded)
    require.NoError(t, err)
    assert.Equal(t, original, decoded)
})
```

**Python** (hypothesis):
```python
from hypothesis import given, strategies as st

@given(st.binary())
def test_base64_roundtrip(data):
    assert base64.b64decode(base64.b64encode(data)) == data
```

**Rust** (proptest):
```rust
proptest! {
    #[test]
    fn base64_roundtrip(data: Vec<u8>) {
        let encoded = base64::encode(&data);
        let decoded = base64::decode(&encoded).unwrap();
        prop_assert_eq!(data, decoded);
    }
}
```

**TypeScript** (fast-check):
```typescript
import fc from 'fast-check';

test('base64 roundtrip', () => {
  fc.assert(fc.property(fc.uint8Array(), (data) => {
    const encoded = Buffer.from(data).toString('base64');
    const decoded = Buffer.from(encoded, 'base64');
    expect(decoded).toEqual(Buffer.from(data));
  }));
});
```

---

## Layer 2: Integration Tests

### testcontainers (real Postgres — all languages)

**Go:**
```go
pg, _ := postgres.Run(ctx, "postgres:16-alpine",
    postgres.WithDatabase("testdb"),
    postgres.WithUsername("test"), postgres.WithPassword("test"))
defer pg.Terminate(ctx)
connStr, _ := pg.ConnectionString(ctx, "sslmode=disable")
db, _ := sql.Open("postgres", connStr)
```

**Python:**
```python
from testcontainers.postgres import PostgresContainer

with PostgresContainer("postgres:16-alpine") as pg:
    engine = create_engine(pg.get_connection_url())
    # run tests with real DB
```

**Rust:**
```rust
let pg = testcontainers::runners::AsyncRunner::start(
    testcontainers_modules::postgres::Postgres::default()
).await;
let conn_str = format!("postgres://postgres:postgres@localhost:{}/postgres", pg.get_host_port_ipv4(5432).await);
```

**TypeScript:**
```typescript
import { PostgreSqlContainer } from '@testcontainers/postgresql';

const pg = await new PostgreSqlContainer('postgres:16-alpine').start();
const connectionUri = pg.getConnectionUri();
```

### Toxiproxy (fault injection — all languages)

Toxiproxy has client libraries for Go, Python, Ruby, .NET, and works via HTTP API
for any language. Pattern:

1. Start Toxiproxy alongside your dependency in testcontainers
2. Create a proxy: `app → toxiproxy:26379 → redis:6379`
3. Add toxics: latency, timeout, reset_peer, bandwidth limit
4. Test that your code handles the failure correctly (timeout, circuit breaker, retry)

---

## Layer 3: E2E / Smoke Tests

### Post-deploy K8s Job (language-agnostic)

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: smoke-test
spec:
  backoffLimit: 3
  activeDeadlineSeconds: 120
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: smoke
        image: curlimages/curl:latest
        command:
        - sh
        - -c
        - |
          set -e
          curl -sf http://my-service/healthz
          curl -sf http://my-service/readyz
          curl -sf http://my-service/api/v1/ping
          echo "Smoke tests passed"
```

### Readiness probe (language-agnostic)

```yaml
readinessProbe:
  httpGet:
    path: /readyz
    port: 8080
  periodSeconds: 10
  failureThreshold: 3
```

Make `/readyz` check real dependencies (DB, Redis, downstream services).
K8s automatically removes unhealthy pods from the Service.

### CronJob synthetic monitoring

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: synthetic-check
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: check
            image: curlimages/curl:latest
            command: ["curl", "-sf", "--max-time", "10", "http://my-service/healthz"]
```

---

## Layer 4: Mutation Testing

| Language | Tool | Command |
|----------|------|---------|
| Go | gremlins | `gremlins unleash ./pkg/core/...` |
| Python | mutmut | `mutmut run --paths-to-mutate=src/core/` |
| Rust | cargo-mutants | `cargo mutants -p my-crate` |
| TypeScript | stryker | `npx stryker run` |

**When to run:** Weekly in CI on critical business logic only (not CRUD handlers).
**Target:** ≥ 80% mutation score for payment, auth, and core modules.
