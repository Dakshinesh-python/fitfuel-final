# FitFuel Backend Test Suite -- Deliverable

This is a complete backend test suite for `fitfuel-final`
(https://github.com/Dakshinesh-python/fitfuel-final), built by cloning and
reading the actual repository (not a generic template), and then run for
real against the actual, unmodified application code.

**465 automated tests, 465 passing (100%), across 9 categories.** 7
genuine security/hygiene findings were discovered and confirmed against a
live running instance in the process -- see `reports/security-review.md`.

## What's in this zip

```
backend-tests/            <- the test suite itself. Copy this whole folder
                              into the repo root, next to backend/, web/,
                              fitfuel_mobile/.
  config.py                  Target URL, endpoint inventory, constants
  conftest.py                 Shared fixtures + report-generation hooks
  utils/payloads.py           SQLi/XSS/command-injection/etc. payload lists
  tests/
    test_authentication.py    63 tests -- register/login/token lifecycle
    test_authorization.py     56 tests -- auth-required matrix, cross-tenant isolation, JWT tampering
    test_input_validation.py  41 tests -- zod schema boundaries
    test_injection.py         86 tests -- SQLi/command/path-traversal/XSS/SSRF/NoSQL payloads
    test_business_logic.py    31 tests -- nutrition math, meal-plan/recommendation rules
    test_configuration.py     30 tests -- security headers, CORS, error handling
    test_functional_api.py    91 tests -- endpoint contracts, round trips
    test_performance.py       30 tests -- response-time budgets, concurrency
    test_dast.py               37 tests -- bypass channels, mass assignment, DoS-shaped payloads
  scripts/generate_reports.py  Turns execution-results.json into every Excel/Markdown report
  load/k6-load-test.js         Sustained-load test (separate from pytest -- see below)
  requirements.txt / pytest.ini

reports/                   <- the actual output from running the suite once,
                              for real, against the live app (see "How these
                              reports were produced" below).
  executive-summary.md        Start here
  security-review.md          Full findings writeup with remediation
  backend-inventory.md        Confirmed stack/endpoint/behavior facts
  performance-report.md       Timing data + concurrency results
  Automation_Test_Report.xlsx Same 6-sheet shape as the sample report you attached
  test-cases.xlsx             Every test case, one row each, with objective/expected/severity
  findings.xlsx                Failed tests + everything tagged [FINDING]
  endpoint-inventory.xlsx      All 19 endpoints + /health
  execution-results.json      Raw machine-readable results (source of truth for the above)
  summary.md                   Short pass/fail summary by category
  logs/backend-tests.log       Full run log

.github/workflows/backend-tests.yml   <- CI pipeline, drop into .github/workflows/
```

## How to run it yourself

1. Copy `backend-tests/` into the repo root (next to `backend/`).
2. Copy `.github/workflows/backend-tests.yml` into `.github/workflows/` if
   you want it in CI (it already matches the same Postgres-service-container
   pattern your existing `backend-ci.yml` uses).
3. Start the real backend against a real database:
   ```bash
   cd backend
   npm install
   npx prisma generate
   npx prisma migrate deploy
   npx prisma db seed   # optional but recommended -- populates the meal catalog
   npm run dev           # or: npm run build && node dist/server.js
   ```
4. In a second terminal:
   ```bash
   cd backend-tests
   pip install -r requirements.txt
   BASE_URL=http://localhost:4000 python3 -m pytest -q
   python3 scripts/generate_reports.py   # regenerates everything in reports/
   ```
5. (Optional) Load test: `BASE_URL=http://localhost:4000 k6 run load/k6-load-test.js`
   (install k6 first: https://grafana.com/docs/k6/latest/set-up/install-k6/)

That's it -- no demo accounts to configure. The suite registers its own
ephemeral test users through the public API at startup (see
`backend-inventory.md` for why: this repo has no auto-seeded accounts,
unlike some templates this suite's structure was informed by).

## How these reports were produced (read this if the numbers matter to you)

The `reports/` folder in this zip is a **real** run, not hand-written
numbers -- but with one caveat worth being upfront about:

The sandbox used to build and validate this suite could not reach Prisma's
binary CDN (`binaries.prisma.sh`) to download the query-engine binary
needed for a real Postgres connection. So the 465-test run that produced
these reports used the actual, unmodified `backend/src/*` application code
(Express routing, zod validation, JWT signing/verification, bcrypt
hashing, the recommendation engine, the nutrition calculator) with only
the Prisma database client swapped for a small in-memory equivalent that
implements the exact same calls the routes actually make (verified by
reading every route file first).

**What this means for you:**
- Every test in this suite talks to the app over real HTTP, exercises real
  middleware and real business logic, and every finding in
  `security-review.md` was independently confirmed against that live
  server before being written up -- they're not guesses from reading code.
- The one thing this run does *not* exercise is the real Postgres query
  layer itself (constraints, indexes, actual SQL). Your existing
  `backend-ci.yml` already provisions real Postgres in GitHub Actions, and
  `.github/workflows/backend-tests.yml` in this zip does the same --
  running the suite there (or locally against a real `DATABASE_URL`, as in
  the steps above) will exercise the real database layer too. Nothing in
  the suite is written to depend on the in-memory stand-in; it's purely an
  artifact of this one validation run.
- If you run it against your real Postgres setup and get different
  results than what's in `reports/`, that's genuinely useful signal (it
  would mean something about the real Postgres/Prisma layer behaves
  differently than the in-memory approximation) -- please treat that as
  worth investigating rather than assuming the suite is wrong.

## The findings, at a glance

| ID | Severity | What |
|---|---|---|
| JWT-1 | Critical | Hardcoded fallback JWT secret if `JWT_SECRET` env var is unset |
| RATE-1 | Medium | No rate limiting on login/register/chat |
| CORS-1 | Medium | CORS defaults to allow-all + credentials when `ALLOWED_ORIGINS` is unset |
| TIMING-1 | Medium | Login response time leaks whether an email is registered |
| BCRYPT-1 | Medium | bcrypt's 72-byte truncation allows password-prefix collisions (library behavior, not a bug, but worth knowing) |
| ERR-1/ERR-2 | Medium/Low | Central error handler returns 500 instead of 400/413 for malformed/oversized bodies |
| EMAIL-1 | Low | No maximum length enforced on the email field |

Full detail and one-line fixes for each are in `reports/security-review.md`.

## A note on the "400+ test cases" ask

This suite has 465 test cases, all real and independently meaningful (not
padded) -- built mostly through deliberate parametrization: e.g. 15 SQL
injection payloads x 3 real unvalidated fields = 45 genuinely distinct
injection tests, 15 protected endpoints x 3 auth-bypass modes = 45 genuine
authorization tests, and so on. Every test has a docstring explaining what
it checks and why, which is also what drives `test-cases.xlsx` --
regenerating that spreadsheet is just re-running
`scripts/generate_reports.py`, no manual spreadsheet maintenance required
as the suite grows.
