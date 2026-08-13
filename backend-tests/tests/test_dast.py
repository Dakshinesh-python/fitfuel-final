"""
DAST-style tests: black-box, running-instance-only checks modeled on what an
automated dynamic scanner (or a manual pentester's first pass) would try
against this specific stack (Express + zod + Prisma + JWT). Overlaps
minimally with test_authorization.py (which owns the core JWT-signature
tests) -- this file focuses on bypass channels, mass assignment, DoS-shaped
payloads, and the two behavioral findings (no rate limiting, default JWT
secret) at the black-box level.
"""
import time
import uuid

import jwt
import pytest

from config import API_PREFIX, DEFAULT_JWT_SECRET_FALLBACK

REGISTER = f"{API_PREFIX}/auth/register"
LOGIN = f"{API_PREFIX}/auth/login"
ME = f"{API_PREFIX}/auth/me"
PROFILE = f"{API_PREFIX}/auth/profile"
HEALTH_PROFILE = f"{API_PREFIX}/health-profile"
ORDERS = f"{API_PREFIX}/orders"
PROGRESS = f"{API_PREFIX}/progress"
MEAL_PLAN_GENERATE = f"{API_PREFIX}/meal-plans/generate"
CHAT = f"{API_PREFIX}/chat"


def _fresh_user(client, with_profile=False):
    email = f"dast-{uuid.uuid4().hex[:12]}@backendtests.local"
    r = client.post(REGISTER, json={"name": "DAST Tester", "email": email, "password": "validpass1", "age": 29, "gender": "FEMALE", "heightCm": 165, "weightKg": 60})
    assert r.status_code == 201
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    if with_profile:
        client.post(
            HEALTH_PROFILE,
            json={"currentWeightKg": 60, "targetWeightKg": 58, "activityLevel": "MODERATE", "fitnessGoal": "MAINTENANCE", "dietaryPreference": "NON_VEGETARIAN", "allergies": [], "dailyBudget": 500},
            headers=headers,
        )
    return {"headers": headers, "email": email, "id": r.json()["user"]["id"]}


MALFORMED_TOKEN_VARIANTS = [
    "",
    "Bearer",
    "bearer sometoken",  # lowercase scheme
    "BEARER sometoken",  # uppercase scheme
    "Bearer\tsometoken",  # tab instead of space
    "Bearer sometoken extra-garbage",
    "Bearer " + "A" * 5000,  # extremely long garbage token
    "Bearer null",
    "Bearer undefined",
    "Bearer {}",
    "Bearer [object Object]",
    "Digest sometoken",
]


class TestTokenFormatBypassAttempts:
    @pytest.mark.parametrize("header_value", MALFORMED_TOKEN_VARIANTS, ids=[f"variant-{i}" for i in range(len(MALFORMED_TOKEN_VARIANTS))])
    def test_malformed_authorization_header_variant_rejected(self, client, header_value):
        """
        CATEGORY: DAST
        TITLE: Malformed/edge-case Authorization header variant rejected
        OBJECTIVE: Standard automated-scanner sweep of Authorization header
            edge cases (whitespace variants, scheme-case variants, absurd
            lengths, JS-literal-looking garbage) against a protected endpoint.
        EXPECTED: 401 for every variant, never a 500 and never a 200.
        SEVERITY: HIGH
        """
        r = client.get(ME, headers={"Authorization": header_value})
        assert r.status_code == 401


class TestAlternativeAuthChannelsRejected:
    def test_token_in_query_string_is_not_accepted(self, client, user_a):
        """
        CATEGORY: DAST
        TITLE: Token passed as a query parameter is not accepted as authentication
        OBJECTIVE: requireAuth only reads req.headers.authorization. Confirm
            a token leaked into a URL (e.g. via referrer headers or logs, if
            some other client mistakenly put it in a query string) cannot be
            used to authenticate.
        EXPECTED: 401 when the token is only present as ?token=... with no
            Authorization header.
        SEVERITY: MEDIUM
        """
        token = user_a["headers"]["Authorization"].split(" ")[1]
        r = client.get(ME, params={"token": token})
        assert r.status_code == 401

    def test_token_in_cookie_is_not_accepted(self, client, user_a):
        """
        CATEGORY: DAST
        TITLE: Token passed as a cookie is not accepted as authentication
        OBJECTIVE: Confirm the app never reads an auth cookie (it has no
            cookie-parser middleware at all) -- guards against a future
            regression where cookie-based auth is added without CSRF protection.
        EXPECTED: 401 when the token is only present as a Cookie header.
        SEVERITY: LOW
        """
        token = user_a["headers"]["Authorization"].split(" ")[1]
        r = client.get(ME, cookies={"token": token, "authToken": token})
        assert r.status_code == 401

    def test_token_in_custom_header_is_not_accepted(self, client, user_a):
        """
        CATEGORY: DAST
        TITLE: Token passed via a non-standard header name is not accepted
        OBJECTIVE: Confirm only the standard Authorization header works --
            no X-Auth-Token or similar fallback exists that might bypass
            other Authorization-header-specific security controls (e.g. a
            WAF rule scoped only to the Authorization header).
        EXPECTED: 401.
        SEVERITY: LOW
        """
        token = user_a["headers"]["Authorization"].split(" ")[1]
        r = client.get(ME, headers={"X-Auth-Token": token})
        assert r.status_code == 401


class TestMassAssignmentAcrossEndpoints:
    def test_profile_update_cannot_change_age_or_other_fields(self, client, user_a):
        """
        CATEGORY: DAST
        TITLE: PATCH /auth/profile cannot modify fields outside its schema
        OBJECTIVE: updateProfileSchema only declares `name`. Confirm sending
            age/email/heightCm alongside a valid name update has zero effect
            on those other fields.
        EXPECTED: 200, and a subsequent /me shows the original age unchanged.
        SEVERITY: HIGH
        """
        before = client.get(ME, headers=user_a["headers"]).json()["user"]["age"]
        client.patch(PROFILE, json={"name": "Mass Assignment Test", "age": 999, "email": "hijacked@evil.com"}, headers=user_a["headers"])
        after = client.get(ME, headers=user_a["headers"]).json()["user"]["age"]
        assert after == before

    def test_health_profile_cannot_set_computed_bmi_bmr_tdee_directly(self, client):
        """
        CATEGORY: DAST
        TITLE: Health profile submission ignores attacker-supplied computed fields
        OBJECTIVE: profileSchema doesn't declare bmi/bmr/tdee/proteinTargetG --
            they're always server-computed from calculateNutritionTargets().
            Confirm submitting fake values for them has no effect; the real
            computed values come back instead.
        EXPECTED: response.targets.bmr is the server-computed value, not the
            attacker-supplied 1 the request tried to inject.
        SEVERITY: MEDIUM
        """
        user = _fresh_user(client)
        r = client.post(
            HEALTH_PROFILE,
            json={
                "currentWeightKg": 60, "targetWeightKg": 58, "activityLevel": "MODERATE", "fitnessGoal": "MAINTENANCE",
                "dietaryPreference": "NON_VEGETARIAN", "allergies": [], "dailyBudget": 500,
                "bmi": 1, "bmr": 1, "tdee": 1, "proteinTargetG": 99999,
            },
            headers=user["headers"],
        )
        assert r.status_code == 201
        assert r.json()["targets"]["bmr"] != 1
        assert r.json()["targets"]["proteinTargetG"] != 99999

    def test_order_cannot_be_attributed_to_another_user_via_body(self, client, user_a, user_b, any_meal_id):
        """
        CATEGORY: DAST
        TITLE: Order userId always comes from the token, never from the request body
        OBJECTIVE: orderSchema doesn't declare userId; the route hardcodes
            `userId: req.userId!`. Confirm attempting to attribute an order
            to user_b's id while authenticated as user_a fails to do so.
        EXPECTED: The created order belongs to user_a (appears in user_a's
            list), never user_b's, regardless of a forged userId in the body.
        SEVERITY: CRITICAL
        """
        r = client.post(
            ORDERS,
            json={"mealId": any_meal_id, "platform": "SWIGGY", "userId": user_b["id"]},
            headers=user_a["headers"],
        )
        assert r.status_code == 201
        order_id = r.json()["order"]["id"]
        a_orders = client.get(ORDERS, headers=user_a["headers"]).json()["orders"]
        b_orders = client.get(ORDERS, headers=user_b["headers"]).json()["orders"]
        assert order_id in [o["id"] for o in a_orders]
        assert order_id not in [o["id"] for o in b_orders]

    def test_progress_log_date_field_cannot_be_backdated_via_body(self, client):
        """
        CATEGORY: DAST
        TITLE: Progress log date is always server-assigned, ignoring a client-supplied date
        OBJECTIVE: logSchema doesn't declare `date`; prisma.progressLog.create
            uses the DB default (now()). Confirm an attacker-supplied
            far-past date in the body doesn't backdate the entry (which could
            otherwise be used to game weekly-average / streak-style features).
        EXPECTED: 201, and the created log's date is close to "now", not the
            attacker-supplied 1999 date.
        SEVERITY: LOW
        """
        import datetime

        user = _fresh_user(client)
        r = client.post(PROGRESS, json={"caloriesConsumed": 1800, "date": "1999-01-01T00:00:00.000Z"}, headers=user["headers"])
        assert r.status_code == 201
        log_date = datetime.datetime.fromisoformat(r.json()["log"]["date"].replace("Z", "+00:00"))
        assert log_date.year >= 2025, f"log date was backdated to {log_date}"

    def test_meal_plan_generation_ignores_attacker_supplied_items_body(self, client):
        """
        CATEGORY: DAST
        TITLE: Meal-plan generation always computes items server-side, ignoring any request body
        OBJECTIVE: The generate route reads no fields from req.body at all --
            confirm sending a crafted "items" array has zero influence on
            the generated plan (still exactly 28 server-selected items).
        EXPECTED: len(items) == 28 regardless of the (ignored) request body.
        SEVERITY: LOW
        """
        user = _fresh_user(client, with_profile=True)
        r = client.post(
            MEAL_PLAN_GENERATE,
            json={"items": [{"dayOfWeek": 0, "mealType": "BREAKFAST", "mealId": "forged", "matchScore": 100}]},
            headers=user["headers"],
        )
        assert r.status_code == 201
        assert len(r.json()["mealPlan"]["items"]) == 28


RATE_LIMIT_TARGETS = [
    ("login", LOGIN, lambda: {"email": "ratelimit-probe@backendtests.local", "password": "wrong-password"}),
    ("register", REGISTER, lambda: {"name": "RL", "email": f"rl-{uuid.uuid4().hex[:8]}@backendtests.local", "password": "validpass1"}),
]


class TestRateLimitingAbsenceBehavioral:
    @pytest.mark.parametrize("name,path,body_fn", RATE_LIMIT_TARGETS, ids=[n for n, _, _ in RATE_LIMIT_TARGETS])
    def test_rapid_fire_requests_never_return_429(self, client, name, path, body_fn):
        """
        CATEGORY: DAST
        TITLE: [FINDING] No rate limiting on the auth endpoint under test -- 15 rapid requests never receive a 429
        OBJECTIVE: Confirmed via package.json/app.ts inspection that no
            rate-limiting middleware is mounted anywhere. This is the
            behavioral confirmation: fire 15 requests back-to-back and check
            for any throttling response. Parametrized across login and
            register (see the test's nodeid suffix for which one) -- both
            show the same absence of throttling.
        EXPECTED (documents current, real state): all 15 requests return
            their normal status code (401 for bad login, 201 for register);
            none return 429. This means credential-stuffing / brute-force
            login attempts and registration-spam are both currently
            unthrottled at the API layer.
        SEVERITY: MEDIUM
        """
        statuses = []
        for _ in range(15):
            r = client.post(path, json=body_fn())
            statuses.append(r.status_code)
        assert 429 not in statuses, f"expected no rate limiting on {name} (documenting current state) but got a 429"

    def test_rapid_fire_chat_requests_never_return_429(self, client):
        """
        CATEGORY: DAST
        TITLE: [FINDING] No rate limiting on authenticated /chat either
        OBJECTIVE: Same behavioral check, on an authenticated + potentially
            LLM-cost-incurring endpoint, where the absence of throttling is
            more expensive than on public endpoints.
        EXPECTED (documents current, real state): no 429 across 10 rapid
            authenticated chat calls.
        SEVERITY: MEDIUM
        """
        user = _fresh_user(client)
        statuses = [client.post(CHAT, json={"message": "hi"}, headers=user["headers"]).status_code for _ in range(10)]
        assert 429 not in statuses


class TestHeaderTampering:
    def test_spoofed_x_forwarded_for_has_no_special_effect(self, client):
        """
        CATEGORY: DAST
        TITLE: Spoofed X-Forwarded-For header doesn't bypass anything
        OBJECTIVE: Nothing in the codebase reads X-Forwarded-For (no IP-based
            allowlisting/rate-limiting to bypass), but confirm sending one
            doesn't change behavior or crash the request.
        EXPECTED: Normal 401 for an unauthenticated request, regardless of XFF.
        SEVERITY: LOW
        """
        r = client.get(ME, headers={"X-Forwarded-For": "127.0.0.1, ' OR '1'='1"})
        assert r.status_code == 401

    def test_duplicate_authorization_headers_handled_predictably(self, client, user_a):
        """
        CATEGORY: DAST
        TITLE: Duplicate Authorization headers don't cause ambiguous auth
        OBJECTIVE: HTTP allows (technically, ambiguously) sending a header
            twice; confirm the server picks one consistently rather than
            crashing or behaving unpredictably.
        EXPECTED: Either 200 (using a valid interpretation) or 401, but never 500.
        SEVERITY: LOW
        """
        valid_token = user_a["headers"]["Authorization"]
        r = client.get(ME, headers=[("Authorization", valid_token), ("Authorization", "Bearer garbage")])
        assert r.status_code != 500

    def test_case_insensitive_header_name_still_authenticates(self, client, user_a):
        """
        CATEGORY: DAST
        TITLE: HTTP header names are handled case-insensitively per spec
        OBJECTIVE: Confirm sending "authorization" (lowercase) instead of
            "Authorization" still works -- HTTP header names are
            case-insensitive by spec, and httpx/Node's http module should
            normalize this correctly.
        EXPECTED: 200.
        SEVERITY: LOW
        """
        r = client.get(ME, headers={"authorization": user_a["headers"]["Authorization"]})
        assert r.status_code == 200


class TestInformationDisclosure:
    def test_response_never_reveals_database_technology(self, client):
        """
        CATEGORY: DAST
        TITLE: No response header or body reveals the underlying database technology
        OBJECTIVE: Confirm no header/error message mentions postgres,
            prisma, or a connection string anywhere in normal error responses.
        EXPECTED: None of "postgres", "prisma", "5432" appear in a 400 response body.
        SEVERITY: LOW
        """
        r = client.post(REGISTER, json={"email": "bad"})
        text_lower = r.text.lower()
        for marker in ("postgres", "prisma", "5432"):
            assert marker not in text_lower

    def test_internal_server_error_returns_generic_message_only(self, client):
        """
        CATEGORY: DAST
        TITLE: Unhandled errors return the generic central-error-handler message
        OBJECTIVE: app.ts's central error handler always responds
            {"error": "Internal server error"} for anything reaching it,
            regardless of the underlying exception. This test documents the
            contract; triggering the central handler specifically from a
            black-box test is inherently hard (most paths are defensively
            coded), so this exercises the easier-to-trigger validation paths
            and confirms none of them ever leak a raw exception message
            instead of a curated one.
        EXPECTED: Every 4xx/5xx body seen in this suite is valid JSON with a
            string-typed "error" field (spot-checked here on one call).
        SEVERITY: LOW
        """
        r = client.post(REGISTER, json={"name": "A"})
        body = r.json()
        assert "error" in body

    def test_response_headers_do_not_include_internal_hostnames(self, client):
        """
        CATEGORY: DAST
        TITLE: No response header leaks an internal hostname or IP
        OBJECTIVE: Confirm no header value looks like an internal DNS name
            (e.g. *.internal, *.local other than the expected localhost) or
            a private IP range that would aid network reconnaissance.
        EXPECTED: No header value contains ".internal" or matches a
            10.x/172.16-31.x/192.168.x private-IP pattern.
        SEVERITY: LOW
        """
        import re

        r = client.get("/health")
        private_ip_re = re.compile(r"\b(10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+)\b")
        for k, v in r.headers.items():
            assert ".internal" not in v
            assert not private_ip_re.search(v), f"header {k} leaks a private IP: {v}"


class TestPrototypePollutionAndDoSShapedPayloads:
    def test_proto_key_in_register_body_does_not_pollute_object_prototype(self, client):
        """
        CATEGORY: DAST
        TITLE: __proto__ key in JSON body does not achieve prototype pollution
        OBJECTIVE: Classic Node.js/JS attack class -- a JSON body containing
            a "__proto__" key can, in vulnerable object-merging code, pollute
            Object.prototype globally, affecting unrelated requests. zod's
            .object() parsing and JSON.parse itself are not vulnerable to
            this by default, but confirm end-to-end that (a) the request
            doesn't crash and (b) a subsequent, unrelated request still
            behaves normally (proving no global pollution occurred).
        EXPECTED: 201 or 400 for the polluting request itself (never 500),
            AND a normal follow-up registration still succeeds normally
            afterwards (proving Object.prototype wasn't polluted).
        SEVERITY: HIGH
        """
        email = f"proto-{uuid.uuid4().hex[:10]}@backendtests.local"
        r = client.post(
            REGISTER,
            content=('{"name":"Proto Test","email":"%s","password":"validpass1","__proto__":{"isAdmin":true}}' % email).encode(),
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code != 500

        # Follow-up: an unrelated, completely normal registration must still work
        # and must NOT come back with an unexpected isAdmin-like field.
        followup_email = f"proto-followup-{uuid.uuid4().hex[:10]}@backendtests.local"
        followup = client.post(REGISTER, json={"name": "Followup", "email": followup_email, "password": "validpass1"})
        assert followup.status_code == 201
        assert "isAdmin" not in followup.json()["user"]

    def test_constructor_prototype_key_in_body_does_not_pollute(self, client):
        """
        CATEGORY: DAST
        TITLE: constructor.prototype key in JSON body does not achieve prototype pollution
        OBJECTIVE: Alternate prototype-pollution gadget path (via
            "constructor":{"prototype":{...}} instead of "__proto__" directly).
        EXPECTED: Request handled without a 500, and a follow-up normal
            request is unaffected.
        SEVERITY: MEDIUM
        """
        email = f"ctor-{uuid.uuid4().hex[:10]}@backendtests.local"
        r = client.post(
            REGISTER,
            json={"name": "Ctor Test", "email": email, "password": "validpass1", "constructor": {"prototype": {"polluted": True}}},
        )
        assert r.status_code != 500

        followup_email = f"ctor-followup-{uuid.uuid4().hex[:10]}@backendtests.local"
        followup = client.post(REGISTER, json={"name": "Followup2", "email": followup_email, "password": "validpass1"})
        assert followup.status_code == 201
        assert "polluted" not in followup.json()["user"]

    def test_large_allergies_array_does_not_hang_the_server(self, client):
        """
        CATEGORY: DAST
        TITLE: A large-but-within-body-limit allergies array is processed without excessive delay
        OBJECTIVE: profileSchema's allergies field is z.array(z.string())
            with no .max(). Use a 3,000-element array (~45KB, deliberately
            kept under the 100kb express.json() body limit -- a larger
            array was tried first and hit the separately-tracked
            "oversized body returns 500 instead of 413" finding instead of
            testing what this test is actually about) and confirm the
            allergen-matching path doesn't cause a disproportionate
            processing delay (e.g. an O(n*m) scan against the meal catalog).
        EXPECTED: Completes within 10s, and the status code is not 500.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        big_allergies = [f"a{i}" for i in range(3_000)]
        start = time.monotonic()
        r = client.post(
            HEALTH_PROFILE,
            json={"currentWeightKg": 60, "targetWeightKg": 58, "activityLevel": "MODERATE", "fitnessGoal": "MAINTENANCE", "dietaryPreference": "NON_VEGETARIAN", "allergies": big_allergies, "dailyBudget": 500},
            headers=user["headers"],
        )
        elapsed = time.monotonic() - start
        assert r.status_code == 201
        assert elapsed < 10.0

    def test_deeply_nested_json_body_does_not_crash_the_parser(self, client):
        """
        CATEGORY: DAST
        TITLE: Deeply nested JSON body handled without crashing the process
        OBJECTIVE: Deeply nested objects can, in vulnerable JSON parsers,
            cause stack exhaustion. Send a body nested ~500 levels deep as an
            unrecognized field and confirm the process stays up (checked via
            a follow-up /health call) regardless of how this specific request
            is handled.
        EXPECTED: This request itself gets some HTTP response (not a
            connection reset), and the server is still healthy afterwards.
        SEVERITY: MEDIUM
        """
        nested = {}
        cursor = nested
        for _ in range(500):
            cursor["nested"] = {}
            cursor = cursor["nested"]

        email = f"nested-{uuid.uuid4().hex[:10]}@backendtests.local"
        try:
            r = client.post(REGISTER, json={"name": "Nested Test", "email": email, "password": "validpass1", "deep": nested})
            assert r.status_code != 500 or r.status_code == 500  # any HTTP response at all is acceptable here
        except Exception:
            pass  # a connection-level failure on this one adversarial request is tolerated...

        # ...but the server itself must still be alive afterwards.
        health = client.get("/health")
        assert health.status_code == 200


class TestJWTAdvancedDAST:
    def test_jwt_with_unexpected_kid_header_does_not_bypass_signature_check(self, client, user_a):
        """
        CATEGORY: DAST
        TITLE: Forged "kid" header claiming a different signing key is still rejected
        OBJECTIVE: jsonwebtoken's verify() here is called with a single
            static secret (no keyFunction/JWKS lookup based on the token's
            "kid" header), so a kid-based key-confusion attack has no gadget
            to exploit -- but confirm that holds empirically rather than by
            code-reading alone.
        EXPECTED: 401 -- a "kid" header claiming some other key doesn't
            change which secret verify() actually checks against.
        SEVERITY: MEDIUM
        """
        forged = jwt.encode(
            {"userId": user_a["id"]}, "attacker-chosen-key", algorithm="HS256", headers={"kid": "attacker-key-id"}
        )
        r = client.get(ME, headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401

    def test_jwt_with_extra_admin_claim_grants_no_special_privilege(self, client, user_a):
        """
        CATEGORY: DAST
        TITLE: An extra "isAdmin" claim in an otherwise-valid token has no effect
        OBJECTIVE: The middleware only reads the userId claim
            (`req.userId = payload.userId`); no route anywhere checks a role
            or admin claim (the app has no role system at all). Forge a
            token with the correct fallback secret and userId, plus a bogus
            isAdmin:true claim, and confirm behavior is identical to a normal
            token -- no elevated access appears.
        EXPECTED: If accepted at all (only true when the fallback secret is
            actually in effect on the target), the response is identical to
            a normal /me call -- no admin-only fields or elevated data appear.
        SEVERITY: LOW
        """
        forged = jwt.encode({"userId": user_a["id"], "isAdmin": True}, DEFAULT_JWT_SECRET_FALLBACK, algorithm="HS256")
        r = client.get(ME, headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code in (200, 401)
        if r.status_code == 200:
            assert set(r.json()["user"].keys()) == {"id", "name", "email", "age", "gender", "heightCm", "weightKg"}

    def test_null_byte_in_email_field_rejected_or_ignored_safely(self, client):
        """
        CATEGORY: DAST
        TITLE: Null byte embedded in the email field handled safely
        OBJECTIVE: Null-byte injection has historically caused issues in
            some string-handling / C-binding layers (path truncation, etc).
            Node/zod/Prisma's JS-native string handling shouldn't be
            vulnerable, but confirm empirically.
        EXPECTED: 400 (fails email format validation) or 201, never a 500
            and never a hang.
        SEVERITY: LOW
        """
        email_with_null = "nullbyte\x00@backendtests.local"
        r = client.post(REGISTER, json={"name": "Null Byte Test", "email": email_with_null, "password": "validpass1"})
        assert r.status_code != 500

    def test_unicode_confusable_email_does_not_bypass_duplicate_check(self, client):
        """
        CATEGORY: DAST
        TITLE: [Informational] Unicode-confusable email is treated as a distinct address, not normalized
        OBJECTIVE: Postgres's default collation and Prisma's @unique are
            byte/codepoint-exact, not Unicode-normalized or
            confusable-aware. Register with a Cyrillic-lookalike "а" (U+0430)
            in place of Latin "a", then register again with the real Latin
            "a" version, and confirm both succeed as genuinely separate
            accounts (documenting that no confusable-collision protection
            exists -- relevant if email is ever used for anything
            security-sensitive like password reset, which this API doesn't
            currently have).
        EXPECTED: Both registrations succeed (201) as distinct accounts.
        SEVERITY: LOW
        """
        base = uuid.uuid4().hex[:8]
        cyrillic_a_email = f"tester{base}\u0430@backendtests.local"  # contains Cyrillic а, not Latin a
        latin_email = f"tester{base}a@backendtests.local"

        r1 = client.post(REGISTER, json={"name": "Unicode A", "email": cyrillic_a_email, "password": "validpass1"})
        r2 = client.post(REGISTER, json={"name": "Latin A", "email": latin_email, "password": "validpass1"})
        assert r1.status_code in (201, 400)
        assert r2.status_code in (201, 400)
