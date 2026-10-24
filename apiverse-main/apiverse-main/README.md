# APIVerse — Autonomous Developer Platform

> **“APIs change. Your code adapts.”**

APIVerse is an AI-assisted developer automation platform that detects API changes in OpenAPI contracts, identifies affected code across client repositories, synthesizes precision repairs, verifies changes through isolated test execution in sandboxes, and prepares reviewable GitHub Pull Requests.

---

## Visual Direction & Design System

APIVerse features a custom, premium dark workspace design system:
- **Canvas & Surfaces:** Near-black base (`#08090D`), deep charcoal surfaces (`#101117`), elevated panels (`#15151D`), and subtle dark borders (`#272832`).
- **Restrained Accents:** Sophisticated violet (`#8B5CF6`), indigo (`#6366F1`), muted emerald for verified states, amber for warnings, and coral/red for breaking changes.
- **Lighting & Depth:** Ambient violet lighting, subtle radial background illumination, and crisp 1px borders.
- **Typography:** Inter and JetBrains Mono for monospace technical paths, AST evidence, and unified diffs.

---

## Architectural Overview

The system operates across eight integrated modules:

1. **API Diff Engine (`backend/app/services/openapi_diff.py`)**:
   - Compares OpenAPI 3.0 / 3.1 specifications in JSON or YAML format.
   - Deterministically detects removed endpoints, removed HTTP methods, removed response properties, type changes, newly required parameters, and removed enum values.
   - Generates exact JSON-pointer evidence and backward compatibility classifications (`BREAKING`, `WARNING`, `INFO`).

2. **Repository Connector (`backend/app/services/github_service.py`)**:
   - Secure GitHub App and Personal Access Token (PAT) server-side integration.
   - Indexes authorized client repositories, retrieves branch trees, and fetches source files.
   - Provides transparent, zero-dependency **Local Demo Mode** for offline demonstration and testing.

3. **Code Impact Analyzer (`backend/app/services/code_impact.py`)**:
   - Language-aware AST analysis for Python and TypeScript/JavaScript clients.
   - Identifies API base URLs, routes, methods, and response property references.
   - Extracts exact file paths, enclosing functions, and line ranges with confidence classification (`confirmed` vs `possible`).

4. **AI Repair Studio (`backend/app/services/ai_repair.py`)**:
   - Modular code repair service supporting configurable LLM providers (`mock` rule engine, `openai`, `anthropic`, `gemini`, `custom`).
   - Generates unified diffs, failure explanations, repair reasoning, and risk assessments.
   - Enforces repository boundary guards and AST syntax validation.

5. **Test Verification Sandbox (`backend/app/services/verifier.py`)**:
   - Executes repository test suites inside isolated sandbox worktree copies.
   - Time, CPU, and filesystem isolated with real-time stdout/stderr capture.
   - Prohibits downstream progression if tests fail or time out.

6. **Pull Request Workflow Engine (`backend/app/services/pr_workflow.py`)**:
   - Explicit workflow state machine: `detected` → `analyzed` → `repaired` → `awaiting_approval` → `verified` → `pr_created`.
   - Dedicated repair branch creation (e.g. `bump/repair-<change-id>-<timestamp>`).
   - Developer approval enforcement and duplicate PR prevention.
   - **Strict Safety Guarantee**: Changes are never automatically merged into default branches.

7. **Scheduled Monitoring & Webhooks (`backend/app/services/monitoring.py`)**:
   - APScheduler-backed recurring specification polling with pause/resume controls.
   - Inbound webhook receivers with HMAC-SHA256 signature verification.
   - Persistent job execution logs and in-app notification center.

8. **Developer Web Application (`frontend/`)**:
   - React 18, TypeScript, Vite, and Tailwind CSS v4.
   - Premium dark technical workspace with interactive diff viewers, code snippet navigators, and live health diagnostics.

---

## Repository Structure

```
d:/BUMP/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # FastAPI REST endpoints
│   │   ├── core/           # Configuration, SQLite database engine
│   │   ├── models/         # Normalized SQLAlchemy models
│   │   ├── schemas/        # Pydantic v2 schemas
│   │   ├── services/       # Core domain engines (diff, impact, repair, verifier, pr, monitoring)
│   │   └── main.py         # Application entry point & lifecycle
│   ├── data/
│   │   ├── bump.db         # Dedicated local SQLite database
│   │   ├── demo_repos/     # Sample Python & TypeScript client repositories
│   │   └── sandbox/        # Isolated test execution scratch worktrees
│   └── tests/              # Comprehensive Pytest test suite
├── frontend/
│   ├── src/
│   │   ├── components/     # APIVerseLogo, Navbar, Sidebar, modals
│   │   ├── services/       # Typed backend API client
│   │   ├── views/          # Subsystem views (Dashboard, Specs, Scans, Impact, Repairs, Tests, PRs, Monitoring, Settings)
│   │   └── types/          # TypeScript interface definitions
│   ├── package.json
│   └── vite.config.ts
├── .env.example
└── README.md
```

---

## Local Setup & Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# From repository root
python -m pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings pyyaml httpx apscheduler pytest

# Copy example environment file
cp .env.example .env

# Run FastAPI backend dev server
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation is available at: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup
```bash
# In frontend directory
cd frontend
npm.cmd install
npm.cmd run dev
```
Developer Platform will be available at: `http://localhost:5173`

---

## Running Automated Tests

Run the full Pytest test suite:
```bash
python -m pytest backend/tests/ -v
```

Build and validate the frontend production bundle:
```bash
cd frontend
npm.cmd run build
```

---

## Operational Verification & Demo Seeding

To verify the complete autonomous workflow instantly:
1. Start backend and frontend.
2. In the top navbar, click **Seed Demo**.
3. Watch the system populate:
   - OpenAPI v1 vs v2 specifications.
   - Breaking change detection (`RESPONSE_PROPERTY_REMOVED`, `ENDPOINT_REMOVED`, etc.).
   - Code impact mapping to `payment-service-py/client.py`.
   - AI repair patch synthesis with unified diff.
   - Test execution verification passing in sandbox.
   - Reviewable Pull Request opened on repair branch.
