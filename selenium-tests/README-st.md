# FitFuel Web — Selenium Test Suite

A 525-test-case Selenium suite for `web/` (the FitFuel React app), designed
to run **entirely inside GitHub Actions** — you never need to install
Chrome, Python, or run anything locally.

```
selenium-tests/
├── config.py                  # BASE_URL, routes, timeouts, auth constants
├── conftest.py                # fixtures, screenshot/console capture, JSON result writer
├── generate_reports.py        # merges results -> Excel / HTML / dashboard / summary
├── pytest.ini
├── requirements.txt
├── page_objects/              # one class per page, real selectors from web/src
│   ├── base_page.py           # shared waits + two-tier auth helper
│   ├── layout.py              # shared nav/logout (every authenticated page)
│   ├── login_page.py / register_page.py
│   ├── dashboard_page.py / health_assessment_page.py / recommendations_page.py
│   ├── progress_page.py / meal_plan_page.py / chat_page.py / profile_page.py
├── utils/
│   ├── driver_factory.py      # headless Chrome via Selenium Manager
│   └── test_data.py           # malformed emails, boundary strings, breakpoints...
└── tests/                     # 12 modules, 525 test cases total
    ├── test_authentication.py      (65 cases)
    ├── test_authorization.py       (70 cases)
    ├── test_navigation.py          (41 cases)
    ├── test_ui_validation.py       (70 cases)
    ├── test_forms.py               (31 cases)
    ├── test_crud_operations.py     (21 cases)
    ├── test_input_validation.py    (92 cases)
    ├── test_error_handling.py      (16 cases)
    ├── test_session_management.py  (22 cases)
    ├── test_downloads_export.py    (12 cases)
    ├── test_accessibility.py       (29 cases)
    └── test_responsive.py          (56 cases)

.github/workflows/selenium-tests.yml   # the CI pipeline (build -> 4-way shard -> merge)
```

Run `pytest --collect-only -q selenium-tests/tests/` yourself and you'll
see exactly **525** collected test cases (confirmed locally before this was
zipped up) — comfortably over your "above 400" requirement, with real
assertions on every one (no `assert True` placeholders anywhere — grep for
`"or True"` / `"assert True"` in `tests/` if you want to double check).

---

## Why "no local execution" actually works here

The trickiest part of testing a GitHub-Pages-deployed SPA entirely from CI
is that **GitHub Pages has no server-side rewrite rule**. `fitfuel-final`
uses React Router's `BrowserRouter` (not `HashRouter`) and ships no
`404.html` SPA-fallback trick, so a direct hit on
`https://<user>.github.io/fitfuel-final/dashboard` on the *real* deployed
site returns a genuine GitHub Pages 404 before React ever loads.

So instead of testing against the live GitHub Pages URL, the CI workflow:

1. **Builds** the app with `npm run build` (produces `web/dist/`).
2. **Serves** it with `npx vite preview --port 4173 --strictPort`. Vite's
   preview server is powered by `sirv` with `single: true`, which *does*
   provide SPA fallback (any unknown path serves `index.html`) — this is
   the standard, documented way to preview a built SPA, and it's why direct
   navigation to `/dashboard`, `/profile`, etc. all work correctly in this
   suite, matching how a properly-configured production SPA host behaves.
3. Runs the whole suite against `http://localhost:4173/fitfuel-final/`.

A `workflow_dispatch` input (`base_url`) lets you re-point the exact same
suite at the real deployed GitHub Pages URL for an occasional production
smoke check, if you ever fix the missing SPA-fallback there.

## Why the suite never depends on your live Render backend

`web/src/api/client.ts` already falls back to `http://localhost:4000` when
`VITE_API_BASE_URL` isn't set at build time — and nothing is listening on
that port in CI. The workflow **deliberately leaves it unset**, so every
real API call fails fast and deterministically. That's a feature, not a
bug: it means

- CI never depends on your Render free-tier backend being awake (no
  cold-start flakiness),
- CI never writes throwaway test accounts into your **real production
  database** on every single push,
- the pipeline stays green and reproducible regardless of backend state.

To still exercise every protected page and route guard without a live
backend, every page object inherits a **two-tier auth helper**
(`BasePage.login_via_ui_or_inject`):

1. **Tier 1 (real):** fills the login form and submits it for real, and
   waits briefly for a redirect to `/dashboard`.
2. **Tier 2 (fallback):** if that doesn't happen within the timeout (the
   expected outcome with no reachable backend), it injects a token directly
   into `localStorage` under the `fitfuel_token` key and navigates to
   `/dashboard` itself.

This works because `RequireAuth` in `web/src/App.tsx` only checks
`localStorage.getItem('fitfuel_token')` truthiness — it never validates the
token client-side. The suite documents and tests this exact behavior
(`test_authorization.py::TestGuestFlagValueStrictness`) rather than
assuming it.

If you ever want a true end-to-end run against your real backend, run the
workflow manually (`workflow_dispatch`) with `base_url` pointed at your live
GitHub Pages site — the real-UI-login tier will then actually succeed end
to end.

## What's tested (and what honestly isn't)

The original brief for this suite (`final_year.md`) included a "File
Upload" test category. **FitFuel's web app has no file upload anywhere** —
verified with `grep -rn 'type="file"' web/src` (zero matches). Rather than
fabricate tests for a feature that doesn't exist, that category was
replaced with **Downloads & Export**, which tests the Meal Plan page's real
Regenerate and Download buttons — the actual closest equivalent feature.

Every other category maps to a real page and real element IDs pulled
directly from the source: `email`/`password` (Login), `name`/`age`/`gender`/
`height`/`weight` (Register), `currentWeight`/`targetWeight`/`dailyBudget`
(Health Assessment), `weightKg`/`caloriesConsumed`/`notes` (Progress),
`profile-first-name`/`profile-save-btn` (Profile), `chat-input`/`chat-send`
(Chat), `meal-plan-regenerate`/`meal-plan-download` (Meal Plan).

Accessibility tests are DOM/keyboard-level checks (label association, alt
text, tab order, heading presence) — this is **not** a substitute for an
axe-core or Lighthouse audit, just a pragmatic Selenium-level pass.

---

## Running it (GitHub Actions — this is the intended path)

1. Copy `selenium-tests/` and `.github/workflows/selenium-tests.yml` into
   your `fitfuel-final` repo root (alongside your existing `web/` and
   `backend/` folders).
2. Commit and push. The workflow triggers automatically on any push/PR that
   touches `web/**` or `selenium-tests/**`, or run it manually from the
   **Actions** tab (`workflow_dispatch`) at any time.
3. Watch it run: **Actions tab → FitFuel Web - Selenium Test Suite**.

The pipeline has three job stages:

| Stage | What it does |
|---|---|
| `build-web` | `npm ci && npm run build`, uploads `web/dist` as an artifact |
| `selenium-tests` (×4, matrix) | Downloads the build, serves it with `vite preview`, installs Chrome, runs its 1/4 slice of the suite (further split across CPU cores with `pytest-xdist`), uploads its raw results |
| `merge-reports` | Downloads all 4 shards' results, merges them, generates the Excel/HTML/dashboard/summary reports, enforces the 90% pass-rate gate, uploads the final `selenium-reports` artifact |

### Downloading your results

After a run finishes, go to the workflow run page → **Artifacts** →
download **`selenium-reports`**. Inside you'll find:

- **`Automation_Test_Report.xlsx`** — 6 sheets: `Executed Tests` (every
  attempt including reruns), `Passed`, `Failed`, `Skipped`,
  `Execution Metrics` (run metadata + pass rate), `Defect Summary`
  (deduplicated failures with a severity rating).
- **`execution-report.html`** — every test attempt in one scrollable table,
  color-coded by status. Open it directly in a browser.
- **`dashboard.html`** — the big pass-rate number plus a per-module bar
  chart. Good for a quick "is it healthy" glance or to show your guide.
- **`execution-results.json`** — the same data as machine-readable JSON, if
  you want to build anything else on top of it.
- **`summary.md`** — a short markdown summary (also posted straight into
  the GitHub Actions job summary page — no need to even open the artifact
  for a quick check).
- **`screenshots/`** — one PNG per *failed* test, filename matches the test
  ID.
- **`logs/`** — one real browser-console log per test (pass or fail) plus
  the full `selenium-tests.log` execution log.

### Adjusting behavior without touching code

All of these are `workflow_dispatch` inputs (Actions tab → Run workflow):

- **`base_url`** — point the suite at a different deployment (e.g. the real
  GitHub Pages URL, or a staging preview).
- **`shards`** — how many parallel matrix jobs to split across (default 4).
- **`reruns`** — automatic reruns per failed test to absorb one-off
  flakiness (default 2).
- **`headless`** — set to `false` if you ever need a debugging run (not
  useful in CI itself, since there's no display, but the option is there).

The pass-rate gate (default 90%) lives in the `merge-reports` job's
`PASS_RATE_GATE` env var — change it there if you want a stricter/looser
threshold. `pass_rate` is computed as `passed / (passed + failed) * 100`
(reruns and skips excluded from the denominator, matching how the sample
report you provided computes it).

---

## Running it locally anyway (optional — not required)

If you ever *do* want to run a quick check on your own machine (e.g. while
iterating on a new test), it works the same way, using your own installed
Chrome:

```bash
cd web && npm ci && npm run build && npx vite preview --port 4173 --strictPort &
cd ../selenium-tests
pip install -r requirements.txt
mkdir -p reports/screenshots reports/logs reports/results
pytest -n auto tests/
python3 generate_reports.py
```

Reports land in `selenium-tests/reports/`, same format as CI.

## Extending the suite

- New page → add a page object in `page_objects/` inheriting from
  `LayoutNav` (if it's behind auth) or `BasePage` (if public), following the
  existing files as a template.
- New route → register it in `config.py`'s `ROUTES` / `PROTECTED_ROUTES` /
  `NAV_ROUTES` as appropriate; several test modules iterate those lists
  automatically via `@pytest.mark.parametrize`, so new routes get picked up
  by Authorization/Navigation/UI Validation/Responsive tests for free.
- New test data set → add to `utils/test_data.py` and parametrize against
  it, same pattern as `MALFORMED_EMAILS` / `BOUNDARY_STRINGS`.
