"""
Authorization tests: every protected endpoint actually enforces requireAuth,
and one user's token can never reach another user's data.

fitfuel-final has no role system and no :id-in-URL resource endpoints for
user-owned data (HealthProfile/MealPlan/Order/ProgressLog are all scoped
internally via req.userId from the JWT, confirmed by reading every route
file) -- so classic "GET /orders/<other-user's-id>" IDOR tests don't apply
here. Instead this file verifies (a) the userId-scoping actually holds by
comparing what user_a and user_b each see, and (b) the token itself can't
be forged, tampered with, or bypassed.
"""
import time

import jwt
import pytest

from config import API_PREFIX, DEFAULT_JWT_SECRET_FALLBACK

# (method, path, minimal json body-or-None) for every requireAuth-protected
# route, confirmed against backend/src/routes/*.ts. Ordering of middleware
# in every one of these files is requireAuth() BEFORE the zod validator, so
# an empty/absent body should never mask a 401 with a 400.
PROTECTED_ENDPOINTS = [
    ("GET",   f"{API_PREFIX}/auth/me", None),
    ("PATCH", f"{API_PREFIX}/auth/profile", {"name": "X"}),
    ("PATCH", f"{API_PREFIX}/auth/password", {"currentPassword": "a", "newPassword": "b"}),
    ("POST",  f"{API_PREFIX}/health-profile", {}),
    ("GET",   f"{API_PREFIX}/health-profile", None),
    ("GET",   f"{API_PREFIX}/recommendations", None),
    ("POST",  f"{API_PREFIX}/meal-plans/generate", {}),
    ("GET",   f"{API_PREFIX}/meal-plans/current", None),
    ("POST",  f"{API_PREFIX}/orders", {}),
    ("GET",   f"{API_PREFIX}/orders", None),
    ("POST",  f"{API_PREFIX}/progress", {}),
    ("GET",   f"{API_PREFIX}/progress/summary", None),
    ("GET",   f"{API_PREFIX}/progress/weight-history", None),
    ("GET",   f"{API_PREFIX}/progress", None),
    ("POST",  f"{API_PREFIX}/chat", {}),
]


def _request(client, method, path, body, headers):
    if body is None:
        return client.request(method, path, headers=headers)
    return client.request(method, path, json=body, headers=headers)


class TestAuthRequiredMatrix:
    @pytest.mark.parametrize(
        "method,path,body", PROTECTED_ENDPOINTS, ids=[f"{m}-{p}" for m, p, _ in PROTECTED_ENDPOINTS]
    )
    def test_endpoint_rejects_missing_token(self, client, method, path, body):
        """
        CATEGORY: Authorization
        TITLE: Protected endpoint rejects requests with no Authorization header
        OBJECTIVE: Confirm requireAuth is actually wired into every route that
            should need it, not just the ones that happen to be tested elsewhere.
        EXPECTED: 401, and never a 200/500.
        SEVERITY: CRITICAL
        """
        r = _request(client, method, path, body, headers={})
        assert r.status_code == 401, f"{method} {path} returned {r.status_code} with no token"

    @pytest.mark.parametrize(
        "method,path,body", PROTECTED_ENDPOINTS, ids=[f"{m}-{p}" for m, p, _ in PROTECTED_ENDPOINTS]
    )
    def test_endpoint_rejects_garbage_token(self, client, method, path, body):
        """
        CATEGORY: Authorization
        TITLE: Protected endpoint rejects a syntactically invalid token
        OBJECTIVE: Same matrix as above, with an obviously-fake Bearer token.
        EXPECTED: 401.
        SEVERITY: CRITICAL
        """
        r = _request(client, method, path, body, headers={"Authorization": "Bearer clearly-not-a-jwt"})
        assert r.status_code == 401, f"{method} {path} returned {r.status_code} with a garbage token"

    @pytest.mark.parametrize(
        "method,path,body", PROTECTED_ENDPOINTS, ids=[f"{m}-{p}" for m, p, _ in PROTECTED_ENDPOINTS]
    )
    def test_endpoint_rejects_token_with_wrong_signature(self, client, method, path, body):
        """
        CATEGORY: Authorization
        TITLE: Protected endpoint rejects a well-formed token signed with the wrong key
        OBJECTIVE: Confirm signature verification happens for every route, not
            just token *shape* checking.
        EXPECTED: 401.
        SEVERITY: CRITICAL
        """
        forged = jwt.encode({"userId": "attacker-controlled-id"}, "not-the-real-secret", algorithm="HS256")
        r = _request(client, method, path, body, headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401, f"{method} {path} returned {r.status_code} with a mis-signed token"


class TestCrossTenantIsolation:
    def test_user_b_health_profile_is_independent_of_user_a(self, client, user_a_with_profile, user_b):
        """
        CATEGORY: Authorization
        TITLE: Health profile is scoped to the authenticated user
        OBJECTIVE: user_a has a completed health profile; confirm user_b -- who
            has not submitted one -- cannot see it through their own token.
        EXPECTED: user_b's GET /health-profile always returns 404 (the route
            has no "empty profile" state -- it's either found for this exact
            userId or 404), and if it were ever 200 the profile's userId must
            not be user_a's.
        SEVERITY: CRITICAL
        """
        r = client.get(f"{API_PREFIX}/health-profile", headers=user_b["headers"])
        assert r.status_code == 404
        if r.status_code == 200:  # defensive: would indicate a serious leak
            assert r.json()["profile"]["userId"] == user_b["id"]

    def test_user_b_orders_never_include_user_a_orders(self, client, user_a_with_profile, user_b, user_b_meal):
        """
        CATEGORY: Authorization
        TITLE: Order history is scoped to the authenticated user
        OBJECTIVE: user_a places an order; confirm user_b's order list never
            contains it.
        EXPECTED: user_a's order id is absent from user_b's GET /orders response.
        SEVERITY: CRITICAL
        """
        order = client.post(
            f"{API_PREFIX}/orders", json={"mealId": user_b_meal, "platform": "SWIGGY"}, headers=user_a_with_profile["headers"]
        )
        assert order.status_code == 201
        order_id = order.json()["order"]["id"]

        b_orders = client.get(f"{API_PREFIX}/orders", headers=user_b["headers"])
        assert b_orders.status_code == 200
        ids = [o["id"] for o in b_orders.json().get("orders", [])]
        assert order_id not in ids

    def test_user_b_progress_log_never_includes_user_a_entries(self, client, user_a_with_profile, user_b):
        """
        CATEGORY: Authorization
        TITLE: Progress logs are scoped to the authenticated user
        OBJECTIVE: user_a logs a progress entry; confirm user_b cannot see it.
        EXPECTED: user_b's GET /progress list length is unaffected by user_a's entry.
        SEVERITY: CRITICAL
        """
        before = client.get(f"{API_PREFIX}/progress", headers=user_b["headers"]).json().get("logs", [])
        create = client.post(
            f"{API_PREFIX}/progress",
            json={"weightKg": 61, "caloriesConsumed": 1800, "proteinConsumedG": 90},
            headers=user_a_with_profile["headers"],
        )
        assert create.status_code == 201
        after = client.get(f"{API_PREFIX}/progress", headers=user_b["headers"]).json().get("logs", [])
        assert len(after) == len(before)

    def test_user_b_current_meal_plan_is_independent_of_user_a(self, client, user_a_with_profile, user_b):
        """
        CATEGORY: Authorization
        TITLE: Meal plans are scoped to the authenticated user
        OBJECTIVE: user_a generates a meal plan; confirm GET /meal-plans/current
            for user_b (no profile, no plan) does not return user_a's plan.
        EXPECTED: user_b's request returns 404 (findFirst scoped to their own
            userId finds nothing), never user_a's plan.
        SEVERITY: CRITICAL
        """
        gen = client.post(f"{API_PREFIX}/meal-plans/generate", headers=user_a_with_profile["headers"])
        assert gen.status_code == 201

        b_current = client.get(f"{API_PREFIX}/meal-plans/current", headers=user_b["headers"])
        assert b_current.status_code == 404

    def test_two_registrations_receive_different_user_ids_and_tokens(self, client, user_a, user_b):
        """
        CATEGORY: Authorization
        TITLE: Distinct accounts get distinct identities
        OBJECTIVE: Sanity check underpinning every other isolation test in this file.
        EXPECTED: user_a and user_b have different ids and different tokens.
        SEVERITY: LOW
        """
        assert user_a["id"] != user_b["id"]
        assert user_a["token"] != user_b["token"]


class TestJWTTamperResistance:
    def test_forged_token_using_documented_default_secret_is_rejected_or_flagged(self, client, user_a):
        """
        CATEGORY: Authorization
        TITLE: [FINDING] Source ships a hardcoded fallback JWT secret
        OBJECTIVE: backend/src/middleware/auth.ts falls back to the literal
            string "dev-secret-change-me" when JWT_SECRET is unset. Confirm
            whether a token forged with that exact fallback string, impersonating
            a real user id, is accepted by the target under test.
        EXPECTED: On a deployment where JWT_SECRET IS set (expected in prod),
            this must be 401 -- the forged token is signed with the wrong key.
            If this instead returns 200, JWT_SECRET is unset and the deployment
            is forgeable by anyone who has read the (public) source code.
            Record the actual outcome in findings.xlsx either way.
        SEVERITY: CRITICAL
        """
        forged = jwt.encode({"userId": user_a["id"]}, DEFAULT_JWT_SECRET_FALLBACK, algorithm="HS256")
        r = client.get(f"{API_PREFIX}/auth/me", headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code in (200, 401)
        # This assertion intentionally does not fail the build either way --
        # its purpose is to make the actual result observable in the report.
        # test_dast.py enforces the hard pass/fail version of this check.

    def test_tampering_with_token_payload_invalidates_signature(self, client, user_a):
        """
        CATEGORY: Authorization
        TITLE: Editing a valid token's payload without re-signing is rejected
        OBJECTIVE: Take a genuinely valid token, flip one character in the
            payload segment (simulating a naive attempt to change userId by
            hand), and confirm the signature check catches it.
        EXPECTED: 401.
        SEVERITY: CRITICAL
        """
        header, payload, sig = user_a["token"].split(".")
        tampered_payload = payload[:-1] + ("A" if payload[-1] != "A" else "B")
        tampered_token = f"{header}.{tampered_payload}.{sig}"
        r = client.get(f"{API_PREFIX}/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
        assert r.status_code == 401

    def test_alg_none_token_is_rejected(self, client, user_a):
        """
        CATEGORY: Authorization
        TITLE: alg:none token forgery is rejected
        OBJECTIVE: Classic JWT library attack -- craft a token with header
            {"alg":"none"} and an empty signature, claiming a real user's id.
            jsonwebtoken's verify() must reject this by default.
        EXPECTED: 401.
        SEVERITY: CRITICAL
        """
        import base64
        import json as _json

        def b64url(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        header = b64url(_json.dumps({"alg": "none", "typ": "JWT"}).encode())
        payload = b64url(_json.dumps({"userId": user_a["id"]}).encode())
        none_token = f"{header}.{payload}."
        r = client.get(f"{API_PREFIX}/auth/me", headers={"Authorization": f"Bearer {none_token}"})
        assert r.status_code == 401

    def test_token_missing_userid_claim_rejected(self, client):
        """
        CATEGORY: Authorization
        TITLE: Token without a userId claim is rejected downstream
        OBJECTIVE: Sign a structurally valid token with the fallback secret but
            omit userId entirely; the route handler's subsequent DB lookup
            should fail closed.
        EXPECTED: 401 or 404 -- never a 200 or an unhandled 500.
        SEVERITY: HIGH
        """
        token = jwt.encode({"notUserId": "x"}, DEFAULT_JWT_SECRET_FALLBACK, algorithm="HS256")
        r = client.get(f"{API_PREFIX}/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code in (401, 404)
        assert r.status_code != 500

    def test_token_with_nonexistent_userid_rejected_cleanly(self, client):
        """
        CATEGORY: Authorization
        TITLE: Token referencing a deleted/nonexistent user handled cleanly
        OBJECTIVE: Sign a token (fallback secret) for a random UUID that was
            never registered. Confirms the route's user-lookup 404-path works
            rather than crashing on a null user.
        EXPECTED: 401 or 404, never 500.
        SEVERITY: MEDIUM
        """
        import uuid as _uuid

        token = jwt.encode({"userId": str(_uuid.uuid4())}, DEFAULT_JWT_SECRET_FALLBACK, algorithm="HS256")
        r = client.get(f"{API_PREFIX}/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code in (401, 404)
        assert r.status_code != 500

    def test_expired_token_rejected_even_for_otherwise_valid_signature(self, client):
        """
        CATEGORY: Authorization
        TITLE: exp claim enforced regardless of endpoint
        OBJECTIVE: Duplicate of the auth-suite expiry check but against a
            second endpoint (/health-profile), confirming expiry isn't only
            checked on one route.
        EXPECTED: 401.
        SEVERITY: MEDIUM
        """
        token = jwt.encode(
            {"userId": "x", "iat": int(time.time()) - 1000, "exp": int(time.time()) - 1},
            DEFAULT_JWT_SECRET_FALLBACK,
            algorithm="HS256",
        )
        r = client.get(f"{API_PREFIX}/health-profile", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 401
