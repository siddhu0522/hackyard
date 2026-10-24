# APIVerse Integration Test Fixture Repository

Dedicated integration-test client repository designed for end-to-end verification of the APIVerse platform:
- **Contract Diffing**: Detecting breaking and non-breaking contract changes across OpenAPI specifications.
- **AST Code Impact Analysis**: Identifying source code references, enclosing functions, and line ranges.
- **AI Repair Studio**: Synthesizing precision unified diffs and handling approval workflows.
- **Sandbox Test Verification**: Executing isolated Pytest test suites.
- **Pull Request Automation**: Generating reviewable PR records targeting non-default branches.

---

## Contract Differences (OpenAPI v1 vs v2)

| # | Change Category | Contract Target | OpenAPI v1 | OpenAPI v2 | Severity | Rule Code |
|---|---|---|---|---|---|---|
| 1 | **Removed Response Property** | `GET /v1/orders/{id}` | `tracking_number: string` (required) | Field removed | `BREAKING` | `BREAKING_PROPERTY_REMOVED` |
| 2 | **Removed Endpoint** | `POST /v1/orders/cancel-legacy` | Endpoint active | Endpoint removed | `BREAKING` | `BREAKING_ENDPOINT_REMOVED` |
| 3 | **Newly Required Parameter** | `POST /v1/orders` | Optional query params | `idempotency_key: string` (required) | `BREAKING` | `BREAKING_REQUIRED_PARAM_ADDED` |
| 4 | **Type Changed** | `POST /v1/orders` (response) | `order_id: integer` | `order_id: string` (UUID) | `BREAKING` | `BREAKING_TYPE_CHANGED` |
| 5 | **Non-Breaking Addition** | `GET /v1/orders/receipt` | Endpoint absent | Endpoint added | `INFO` | `INFO_ENDPOINT_ADDED` |
| 6 | **Non-Breaking Field** | `POST /v1/orders` (body) | Absent | Optional `notes: string` | `INFO` | `INFO_PROPERTY_ADDED` |

---

## Client Code Mapping & Impact Surface

The client code in `client.py` references each affected endpoint:
1. `get_order(order_id)`:
   - File: `client.py` (Lines ~17–38)
   - References `data["tracking_number"]`
   - Confidence: `confirmed`
2. `cancel_order_legacy(order_id, reason)`:
   - File: `client.py` (Lines ~40–58)
   - Calls removed route `/v1/orders/cancel-legacy`
   - Confidence: `confirmed`
3. `create_order(amount, items)`:
   - File: `client.py` (Lines ~60–80)
   - Calls `/v1/orders` without sending mandatory `idempotency_key`
   - Confidence: `confirmed`

---

## Test Suite Execution

Run tests locally:
```bash
python -m pytest tests/test_client.py -v
```
All tests pass against the baseline v1 contract specification.
