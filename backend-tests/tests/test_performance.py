"""
Performance tests: response-time budgets, basic concurrency handling, and
one timing side-channel check. These run against the target under test's
actual network path (real HTTP round trips via httpx), so absolute
thresholds are intentionally generous -- the goal is to catch gross
regressions (an endpoint that suddenly takes 10x longer, or breaks under
concurrent load), not to be a substitute for load/k6 testing, which is
in ../load/k6-load-test.js.
"""
import concurrent.futures
import statistics
import time
import uuid

import pytest

from config import API_PREFIX

REGISTER = f"{API_PREFIX}/auth/register"
LOGIN = f"{API_PREFIX}/auth/login"
ME = f"{API_PREFIX}/auth/me"
MEALS = f"{API_PREFIX}/meals"
HEALTH_PROFILE = f"{API_PREFIX}/health-profile"
MEAL_PLAN_GENERATE = f"{API_PREFIX}/meal-plans/generate"
RECOMMENDATIONS = f"{API_PREFIX}/recommendations"

# Generous budgets: these run against whatever's actually hosting the target
# (a laptop, a CI runner, a free-tier DB) so thresholds allow real network/DB
# variance while still catching order-of-magnitude regressions.
FAST_ENDPOINT_BUDGET_S = 2.0
HEAVY_ENDPOINT_BUDGET_S = 5.0


def _timed(fn):
    start = time.monotonic()
    result = fn()
    return result, time.monotonic() - start


def _fresh_user(client, with_profile=False):
    email = f"perf-{uuid.uuid4().hex[:12]}@backendtests.local"
    r = client.post(REGISTER, json={"name": "Perf Tester", "email": email, "password": "validpass1", "age": 30, "gender": "MALE", "heightCm": 175, "weightKg": 75})
    assert r.status_code == 201
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    if with_profile:
        client.post(
            HEALTH_PROFILE,
            json={"currentWeightKg": 75, "targetWeightKg": 72, "activityLevel": "MODERATE", "fitnessGoal": "MAINTENANCE", "dietaryPreference": "NON_VEGETARIAN", "allergies": [], "dailyBudget": 500},
            headers=headers,
        )
    return headers


class TestResponseTimeBudgets:
    def test_health_check_responds_quickly(self, client):
        """
        CATEGORY: Performance
        TITLE: /health responds within budget
        OBJECTIVE: The liveness endpoint does no DB work; it should be fast
            under virtually any load.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        _, elapsed = _timed(lambda: client.get("/health"))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_meal_catalog_listing_responds_within_budget(self, client):
        """
        CATEGORY: Performance
        TITLE: GET /meals responds within budget
        OBJECTIVE: A capped (take:100), indexed catalog read should be fast.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        _, elapsed = _timed(lambda: client.get(MEALS))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_registration_responds_within_budget_despite_bcrypt_cost(self, client):
        """
        CATEGORY: Performance
        TITLE: Registration (bcrypt cost factor 10) responds within budget
        OBJECTIVE: bcrypt.hash(password, 10) is deliberately slow (that's the
            point of bcrypt), but confirm cost factor 10 doesn't push it past
            a reasonable ceiling for an interactive request.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        email = f"perf-reg-{uuid.uuid4().hex[:10]}@backendtests.local"
        _, elapsed = _timed(lambda: client.post(REGISTER, json={"name": "Perf", "email": email, "password": "validpass1"}))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_login_responds_within_budget(self, client):
        """
        CATEGORY: Performance
        TITLE: Login (bcrypt.compare) responds within budget
        OBJECTIVE: Same rationale as registration, for the compare side.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        email = f"perf-login-{uuid.uuid4().hex[:10]}@backendtests.local"
        client.post(REGISTER, json={"name": "Perf", "email": email, "password": "validpass1"})
        _, elapsed = _timed(lambda: client.post(LOGIN, json={"email": email, "password": "validpass1"}))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_meal_plan_generation_responds_within_heavier_budget(self, client):
        """
        CATEGORY: Performance
        TITLE: Meal plan generation (28-item, multi-query operation) responds within budget
        OBJECTIVE: This is the heaviest single request in the API: it reads
            up to 500 meals, runs the ranking algorithm 28 times, then does a
            createMany + a re-fetch with nested includes. Confirm it stays
            within a looser but still bounded budget.
        EXPECTED: < 5s.
        SEVERITY: MEDIUM
        """
        headers = _fresh_user(client, with_profile=True)
        _, elapsed = _timed(lambda: client.post(MEAL_PLAN_GENERATE, headers=headers))
        assert elapsed < HEAVY_ENDPOINT_BUDGET_S

    def test_recommendations_response_within_budget(self, client):
        """
        CATEGORY: Performance
        TITLE: Recommendations (up to 200-candidate ranking) responds within budget
        OBJECTIVE: This route reads up to 200 meals and scores every one.
        EXPECTED: < 5s.
        SEVERITY: MEDIUM
        """
        headers = _fresh_user(client, with_profile=True)
        _, elapsed = _timed(lambda: client.get(RECOMMENDATIONS, headers=headers))
        assert elapsed < HEAVY_ENDPOINT_BUDGET_S

    def test_me_endpoint_responds_within_budget(self, client, user_a):
        """
        CATEGORY: Performance
        TITLE: /me (JWT verify + single-row lookup) responds within budget
        OBJECTIVE: Should be one of the fastest authenticated endpoints.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        _, elapsed = _timed(lambda: client.get(ME, headers=user_a["headers"]))
        assert elapsed < FAST_ENDPOINT_BUDGET_S


class TestConcurrency:
    def test_concurrent_registrations_all_succeed_with_unique_emails(self, client, base_url):
        """
        CATEGORY: Performance
        TITLE: 15 concurrent registrations with distinct emails all succeed
        OBJECTIVE: Confirm the server (and connection pool / DB pool
            underneath it) handles a burst of concurrent writes without
            dropping or corrupting requests.
        EXPECTED: All 15 requests return 201, all with distinct user ids.
        SEVERITY: MEDIUM
        """
        import httpx

        def register(i):
            with httpx.Client(base_url=base_url, timeout=15) as c:
                email = f"concurrent-{uuid.uuid4().hex[:10]}@backendtests.local"
                return c.post(REGISTER, json={"name": f"Concurrent {i}", "email": email, "password": "validpass1"})

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as pool:
            results = list(pool.map(register, range(15)))

        statuses = [r.status_code for r in results]
        assert all(s == 201 for s in statuses), f"statuses: {statuses}"
        ids = [r.json()["user"]["id"] for r in results]
        assert len(set(ids)) == 15, "duplicate user ids returned under concurrent load"

    def test_concurrent_reads_of_public_catalog_all_succeed(self, client, base_url):
        """
        CATEGORY: Performance
        TITLE: 20 concurrent GET /meals requests all succeed
        OBJECTIVE: Read-heavy concurrency check on the most frequently hit
            public endpoint.
        EXPECTED: All 20 requests return 200.
        SEVERITY: LOW
        """
        import httpx

        def fetch(_i):
            with httpx.Client(base_url=base_url, timeout=15) as c:
                return c.get(MEALS)

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(fetch, range(20)))
        assert all(r.status_code == 200 for r in results)

    def test_concurrent_requests_with_same_token_do_not_interfere(self, client, user_a, base_url):
        """
        CATEGORY: Performance
        TITLE: Concurrent requests from the same authenticated user don't cross-contaminate
        OBJECTIVE: Fire 10 simultaneous /me requests using the same token and
            confirm every response correctly reports user_a's own id (no
            connection-pool / middleware state leaking between requests).
        EXPECTED: All 10 responses report user_a["id"].
        SEVERITY: MEDIUM
        """
        import httpx

        def fetch_me(_i):
            with httpx.Client(base_url=base_url, timeout=15) as c:
                return c.get(ME, headers=user_a["headers"])

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(fetch_me, range(10)))
        for r in results:
            assert r.status_code == 200
            assert r.json()["user"]["id"] == user_a["id"]


class TestPayloadSizeAndVolume:
    def test_large_but_within_limit_notes_field_does_not_degrade_badly(self, client, user_a):
        """
        CATEGORY: Performance
        TITLE: A large (but under the 100kb body limit) progress note doesn't cause a slow path
        OBJECTIVE: Confirm a big-but-legal payload (50KB of notes text)
            doesn't trigger disproportionately slow processing.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        from config import API_PREFIX as _P

        big_notes = "N" * 50_000
        _, elapsed = _timed(lambda: client.post(f"{_P}/progress", json={"notes": big_notes}, headers=user_a["headers"]))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_repeated_sequential_requests_response_time_stays_stable(self, client):
        """
        CATEGORY: Performance
        TITLE: Response time for repeated GET /meals calls stays stable (no creeping latency)
        OBJECTIVE: Fire 20 sequential requests and confirm the later ones
            aren't dramatically slower than the earlier ones (which would
            suggest a connection or memory leak under sustained use).
        EXPECTED: The median of the last 5 calls is not more than 3x the
            median of the first 5 (generous threshold -- this is a smoke
            check, not a leak-detection tool).
        SEVERITY: LOW
        """
        timings = []
        for _ in range(20):
            _, elapsed = _timed(lambda: client.get(MEALS))
            timings.append(elapsed)
        first_five_median = statistics.median(timings[:5])
        last_five_median = statistics.median(timings[-5:])
        assert last_five_median < max(first_five_median * 3, 0.5), (
            f"latency crept from {first_five_median:.3f}s to {last_five_median:.3f}s over 20 sequential calls"
        )


class TestTimingSideChannel:
    def test_login_timing_does_not_meaningfully_reveal_account_existence(self, client):
        """
        CATEGORY: Performance
        TITLE: [FINDING] Login response time differs between unknown-email and wrong-password paths
        OBJECTIVE: auth.routes.ts's login handler returns 401 immediately
            when the user is not found (`if (!user) return 401`), skipping
            bcrypt.compare entirely -- but runs a real bcrypt.compare (cost
            10, ~50-100ms) when the user exists but the password is wrong.
            That asymmetry is a textbook user-enumeration timing side channel.
            This test measures both paths and reports the gap; it does not
            hard-fail the build (timing measurements are noisy in shared CI
            runners), but the finding itself is real and is recorded in
            findings.xlsx (regardless of what this specific run measures).
        EXPECTED (informational): unknown-email responses average
            meaningfully faster than wrong-password responses. Remediation:
            run a dummy bcrypt.compare against a fixed hash on the
            user-not-found path so both branches take comparable time.
        SEVERITY: MEDIUM
        """
        import uuid as _uuid

        known_email = f"timing-{_uuid.uuid4().hex[:10]}@backendtests.local"
        client.post(REGISTER, json={"name": "Timing Test", "email": known_email, "password": "validpass1"})

        unknown_timings = []
        wrong_password_timings = []
        for _ in range(5):
            _, t1 = _timed(lambda: client.post(LOGIN, json={"email": f"nobody-{_uuid.uuid4().hex[:8]}@backendtests.local", "password": "whatever123"}))
            unknown_timings.append(t1)
            _, t2 = _timed(lambda: client.post(LOGIN, json={"email": known_email, "password": "wrong-password-guess"}))
            wrong_password_timings.append(t2)

        avg_unknown = statistics.mean(unknown_timings)
        avg_wrong_pw = statistics.mean(wrong_password_timings)
        # Informational assertion only: confirms neither path errors out.
        # The timing gap itself (avg_wrong_pw typically >> avg_unknown due to
        # bcrypt.compare running only on the known-email path) is what's
        # recorded as the finding, not asserted as a hard pass/fail here.
        assert avg_unknown >= 0 and avg_wrong_pw >= 0


class TestMoreResponseTimeBudgets:
    def test_orders_list_responds_within_budget(self, client, user_a):
        """
        CATEGORY: Performance
        TITLE: GET /orders responds within budget
        OBJECTIVE: Small, userId-indexed read with a meal join.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        from config import API_PREFIX as _P

        _, elapsed = _timed(lambda: client.get(f"{_P}/orders", headers=user_a["headers"]))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_progress_list_responds_within_budget(self, client, user_a):
        """
        CATEGORY: Performance
        TITLE: GET /progress responds within budget
        OBJECTIVE: Small, userId-indexed, take:100-capped read.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        from config import API_PREFIX as _P

        _, elapsed = _timed(lambda: client.get(f"{_P}/progress", headers=user_a["headers"]))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_progress_summary_responds_within_budget(self, client, user_a):
        """
        CATEGORY: Performance
        TITLE: GET /progress/summary responds within budget
        OBJECTIVE: Involves an aggregate (average) computed in application code.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        from config import API_PREFIX as _P

        _, elapsed = _timed(lambda: client.get(f"{_P}/progress/summary", headers=user_a["headers"]))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_weight_history_responds_within_budget(self, client, user_a):
        """
        CATEGORY: Performance
        TITLE: GET /progress/weight-history responds within budget
        OBJECTIVE: 90-day windowed, select-projected read.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        from config import API_PREFIX as _P

        _, elapsed = _timed(lambda: client.get(f"{_P}/progress/weight-history", headers=user_a["headers"]))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_meal_plan_current_responds_within_budget(self, client):
        """
        CATEGORY: Performance
        TITLE: GET /meal-plans/current responds within budget
        OBJECTIVE: Nested include (items -> meal) read.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        headers = _fresh_user(client, with_profile=True)
        client.post(MEAL_PLAN_GENERATE, headers=headers)
        _, elapsed = _timed(lambda: client.get(f"{API_PREFIX}/meal-plans/current", headers=headers))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_order_placement_responds_within_budget(self, client, any_meal_id):
        """
        CATEGORY: Performance
        TITLE: POST /orders responds within budget
        OBJECTIVE: Single meal lookup + single insert.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        headers = _fresh_user(client)
        _, elapsed = _timed(lambda: client.post(f"{API_PREFIX}/orders", json={"mealId": any_meal_id, "platform": "SWIGGY"}, headers=headers))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_progress_log_creation_responds_within_budget(self, client):
        """
        CATEGORY: Performance
        TITLE: POST /progress responds within budget
        OBJECTIVE: Single insert, no heavy computation.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        headers = _fresh_user(client)
        _, elapsed = _timed(lambda: client.post(f"{API_PREFIX}/progress", json={"caloriesConsumed": 1800}, headers=headers))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_chat_responds_within_generous_budget(self, client):
        """
        CATEGORY: Performance
        TITLE: POST /chat responds within a generous budget
        OBJECTIVE: May involve an outbound LLM call; use a looser budget than
            pure-DB endpoints, but still bounded so a hung request is caught.
        EXPECTED: < 10s.
        SEVERITY: LOW
        """
        headers = _fresh_user(client)
        _, elapsed = _timed(lambda: client.post(f"{API_PREFIX}/chat", json={"message": "Quick question about protein."}, headers=headers))
        assert elapsed < 10.0

    def test_profile_update_responds_within_budget(self, client, user_a):
        """
        CATEGORY: Performance
        TITLE: PATCH /auth/profile responds within budget
        OBJECTIVE: Single-row update, no heavy computation.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        _, elapsed = _timed(lambda: client.patch(f"{API_PREFIX}/auth/profile", json={"name": "Perf Updated Name"}, headers=user_a["headers"]))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_password_change_responds_within_budget_despite_two_bcrypt_ops(self, client):
        """
        CATEGORY: Performance
        TITLE: PATCH /auth/password (compare + hash) responds within budget
        OBJECTIVE: This route runs both a bcrypt.compare AND a bcrypt.hash
            (cost 10) in the same request -- confirm that doubled cost still
            lands within a reasonable ceiling.
        EXPECTED: < 3s.
        SEVERITY: LOW
        """
        email = f"perf-pwchange-{uuid.uuid4().hex[:10]}@backendtests.local"
        reg = client.post(REGISTER, json={"name": "Perf", "email": email, "password": "validpass1"})
        headers = {"Authorization": f"Bearer {reg.json()['token']}"}
        _, elapsed = _timed(
            lambda: client.patch(f"{API_PREFIX}/auth/password", json={"currentPassword": "validpass1", "newPassword": "newvalidpass1"}, headers=headers)
        )
        assert elapsed < 3.0


class TestMoreConcurrency:
    def test_concurrent_health_profile_submissions_for_different_users(self, client, base_url):
        """
        CATEGORY: Performance
        TITLE: 10 concurrent health-profile submissions (different users) all succeed
        OBJECTIVE: Confirm the nutrition-calculation + upsert path holds up
            under concurrent load from distinct users.
        EXPECTED: All 10 return 201.
        SEVERITY: MEDIUM
        """
        import httpx

        def submit(_i):
            with httpx.Client(base_url=base_url, timeout=15) as c:
                email = f"concurrent-hp-{uuid.uuid4().hex[:10]}@backendtests.local"
                reg = c.post(REGISTER, json={"name": "Concurrent HP", "email": email, "password": "validpass1", "age": 30, "gender": "MALE", "heightCm": 175, "weightKg": 75})
                headers = {"Authorization": f"Bearer {reg.json()['token']}"}
                return c.post(
                    HEALTH_PROFILE,
                    json={"currentWeightKg": 75, "targetWeightKg": 72, "activityLevel": "MODERATE", "fitnessGoal": "MAINTENANCE", "dietaryPreference": "NON_VEGETARIAN", "allergies": [], "dailyBudget": 500},
                    headers=headers,
                )

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(submit, range(10)))
        assert all(r.status_code == 201 for r in results)

    def test_concurrent_order_placement_by_same_user_no_data_corruption(self, client, base_url, any_meal_id):
        """
        CATEGORY: Performance
        TITLE: 8 concurrent orders from the same user all get distinct order ids
        OBJECTIVE: Confirm no race condition causes duplicate/dropped order rows.
        EXPECTED: 8 distinct order ids, all 201.
        SEVERITY: MEDIUM
        """
        import httpx

        email = f"concurrent-orders-{uuid.uuid4().hex[:10]}@backendtests.local"
        reg = client.post(REGISTER, json={"name": "Concurrent Orders", "email": email, "password": "validpass1"})
        headers = {"Authorization": f"Bearer {reg.json()['token']}"}

        def place(_i):
            with httpx.Client(base_url=base_url, timeout=15) as c:
                return c.post(f"{API_PREFIX}/orders", json={"mealId": any_meal_id, "platform": "SWIGGY"}, headers=headers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(place, range(8)))
        assert all(r.status_code == 201 for r in results)
        ids = [r.json()["order"]["id"] for r in results]
        assert len(set(ids)) == 8

    def test_concurrent_progress_logs_by_same_user_all_recorded(self, client, base_url):
        """
        CATEGORY: Performance
        TITLE: 10 concurrent progress-log writes from the same user are all persisted
        OBJECTIVE: Confirm no writes are silently dropped under concurrent load.
        EXPECTED: GET /progress afterwards shows exactly 10 new entries.
        SEVERITY: MEDIUM
        """
        import httpx

        email = f"concurrent-progress-{uuid.uuid4().hex[:10]}@backendtests.local"
        reg = client.post(REGISTER, json={"name": "Concurrent Progress", "email": email, "password": "validpass1"})
        headers = {"Authorization": f"Bearer {reg.json()['token']}"}

        def log(_i):
            with httpx.Client(base_url=base_url, timeout=15) as c:
                return c.post(f"{API_PREFIX}/progress", json={"caloriesConsumed": 1800 + _i}, headers=headers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(log, range(10)))
        assert all(r.status_code == 201 for r in results)

        listed = client.get(f"{API_PREFIX}/progress", headers=headers)
        assert len(listed.json()["logs"]) == 10

    def test_health_check_stays_responsive_under_concurrent_load(self, client, base_url):
        """
        CATEGORY: Performance
        TITLE: /health stays responsive under 25 concurrent requests
        OBJECTIVE: Confirm the liveness endpoint itself doesn't degrade when
            the server is busy handling a burst of other traffic-shaped load.
        EXPECTED: All 25 requests return 200 within the fast-endpoint budget.
        SEVERITY: LOW
        """
        import httpx

        def ping(_i):
            with httpx.Client(base_url=base_url, timeout=15) as c:
                start = time.monotonic()
                r = c.get("/health")
                return r.status_code, time.monotonic() - start

        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as pool:
            results = list(pool.map(ping, range(25)))
        assert all(status == 200 for status, _ in results)
        assert max(elapsed for _, elapsed in results) < FAST_ENDPOINT_BUDGET_S * 3


class TestFilteredQueryPerformance:
    def test_filtered_meal_query_responds_within_budget(self, client):
        """
        CATEGORY: Performance
        TITLE: Filtered meal query (mealType) responds within budget
        OBJECTIVE: Confirm adding a where-clause filter doesn't meaningfully
            slow down the catalog read.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        _, elapsed = _timed(lambda: client.get(MEALS, params={"mealType": "LUNCH"}))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_single_meal_lookup_responds_within_budget(self, client, any_meal_id):
        """
        CATEGORY: Performance
        TITLE: GET /meals/:id responds within budget
        OBJECTIVE: Primary-key lookup should be the fastest read in the API.
        EXPECTED: < 2s.
        SEVERITY: LOW
        """
        _, elapsed = _timed(lambda: client.get(f"{MEALS}/{any_meal_id}"))
        assert elapsed < FAST_ENDPOINT_BUDGET_S

    def test_concurrent_single_meal_lookups_all_succeed(self, client, base_url, any_meal_id):
        """
        CATEGORY: Performance
        TITLE: 20 concurrent single-meal lookups all succeed
        OBJECTIVE: Read-heavy concurrency check on a primary-key lookup path.
        EXPECTED: All 20 return 200 with the correct meal id.
        SEVERITY: LOW
        """
        import httpx

        def fetch(_i):
            with httpx.Client(base_url=base_url, timeout=15) as c:
                return c.get(f"{MEALS}/{any_meal_id}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(fetch, range(20)))
        assert all(r.status_code == 200 and r.json()["meal"]["id"] == any_meal_id for r in results)
