"""
Configuration/hardening tests: security headers (helmet), CORS behavior,
error-handling info-leak checks, cookie usage, and other deployment-level
concerns. Header values here were captured directly from a live run of the
actual app (see reports/backend-inventory.md, "Confirmed response headers")
before being encoded as assertions.
"""
import json

import pytest

from config import API_PREFIX

HEALTH = "/health"
REGISTER = f"{API_PREFIX}/auth/register"
LOGIN = f"{API_PREFIX}/auth/login"
ME = f"{API_PREFIX}/auth/me"

EXPECTED_HELMET_HEADERS = [
    ("x-content-type-options", "nosniff"),
    ("x-frame-options", "SAMEORIGIN"),
    ("x-dns-prefetch-control", "off"),
    ("x-download-options", "noopen"),
    ("x-permitted-cross-domain-policies", "none"),
    ("referrer-policy", "no-referrer"),
    ("cross-origin-opener-policy", "same-origin"),
    ("cross-origin-resource-policy", "same-origin"),
    ("x-xss-protection", "0"),  # helmet intentionally disables the legacy header (0), not "1; mode=block"
]

CSP_DIRECTIVES = ["default-src 'self'", "object-src 'none'", "frame-ancestors 'self'", "script-src 'self'"]


class TestSecurityHeaders:
    @pytest.mark.parametrize("header,expected_value", EXPECTED_HELMET_HEADERS, ids=[h for h, _ in EXPECTED_HELMET_HEADERS])
    def test_helmet_header_present_with_expected_value(self, client, header, expected_value):
        """
        CATEGORY: Configuration
        TITLE: helmet security header set with the expected value
        OBJECTIVE: app.ts calls app.use(helmet()) with defaults. Confirm each
            standard helmet header is actually present on real responses.
        EXPECTED: Header present, value matches helmet's documented default.
        SEVERITY: MEDIUM
        """
        r = client.get(HEALTH)
        assert header in {k.lower(): v for k, v in r.headers.items()}
        assert r.headers.get(header) == expected_value

    def test_strict_transport_security_header_present(self, client):
        """
        CATEGORY: Configuration
        TITLE: HSTS header present
        OBJECTIVE: Confirm Strict-Transport-Security is set (helmet default:
            max-age=15552000; includeSubDomains).
        EXPECTED: Header present and includes "max-age=".
        SEVERITY: MEDIUM
        """
        r = client.get(HEALTH)
        assert "max-age=" in r.headers.get("strict-transport-security", "")

    @pytest.mark.parametrize("directive", CSP_DIRECTIVES, ids=[d.split()[0] for d in CSP_DIRECTIVES])
    def test_content_security_policy_directive_present(self, client, directive):
        """
        CATEGORY: Configuration
        TITLE: CSP includes a restrictive directive
        OBJECTIVE: Confirm specific CSP directives from helmet's default
            policy are present (not just that the header exists at all).
        EXPECTED: The directive substring appears in the CSP header value.
        SEVERITY: MEDIUM
        """
        r = client.get(HEALTH)
        csp = r.headers.get("content-security-policy", "")
        assert directive in csp

    def test_x_powered_by_header_removed(self, client):
        """
        CATEGORY: Configuration
        TITLE: X-Powered-By: Express header is not leaked
        OBJECTIVE: helmet() removes Express's default X-Powered-By header,
            which otherwise reveals the backend framework to any caller.
        EXPECTED: "x-powered-by" absent from response headers.
        SEVERITY: LOW
        """
        r = client.get(HEALTH)
        assert "x-powered-by" not in {k.lower() for k in r.headers.keys()}

    def test_no_framework_name_leaked_anywhere_in_headers(self, client):
        """
        CATEGORY: Configuration
        TITLE: No header value contains the word "Express"
        OBJECTIVE: Broader sweep beyond the specific X-Powered-By check --
            confirm no other header (e.g. a custom error handler) leaks the
            framework name.
        EXPECTED: No header value (case-insensitive) contains "express".
        SEVERITY: LOW
        """
        r = client.get(HEALTH)
        for k, v in r.headers.items():
            assert "express" not in v.lower(), f"header {k}: {v} leaks framework name"


class TestCORSConfiguration:
    def test_cors_never_reflects_an_arbitrary_origin_together_with_credentials(self, client):
        """
        CATEGORY: Configuration
        TITLE: [FINDING] CORS must never combine origin-reflection with credentials:true for an untrusted origin
        OBJECTIVE: backend/src/app.ts's getAllowedOrigins() defaults to `true`
            (reflect-any-origin) when ALLOWED_ORIGINS is unset, logging a
            warning but still allowing it -- and cors({credentials:true})
            means that reflected origin can also send credentialed requests.
            Confirmed directly (see backend-inventory.md) that with
            ALLOWED_ORIGINS unset, a request from http://evil.example.com
            gets back Access-Control-Allow-Origin: http://evil.example.com
            AND Access-Control-Allow-Credentials: true simultaneously.
        EXPECTED: For a deployment with ALLOWED_ORIGINS correctly configured
            (the documented production requirement), an untrusted origin must
            NOT receive both headers together. If this test fails, either
            ALLOWED_ORIGINS is unset on the target, or an origin allowlist
            entry is broader than intended -- both are real deployment bugs,
            not test bugs.
        SEVERITY: MEDIUM
        """
        evil_origin = "http://evil-attacker-site.example"
        r = client.get(HEALTH, headers={"Origin": evil_origin})
        acao = r.headers.get("access-control-allow-origin")
        acac = r.headers.get("access-control-allow-credentials")
        assert not (acao == evil_origin and acac == "true"), (
            f"CORS reflects untrusted origin {evil_origin!r} with credentials enabled -- "
            f"set ALLOWED_ORIGINS in this environment. See findings.xlsx (CORS-1)."
        )

    def test_cors_preflight_options_request_succeeds(self, client):
        """
        CATEGORY: Configuration
        TITLE: CORS preflight (OPTIONS) requests are handled
        OBJECTIVE: Confirm the cors middleware answers OPTIONS requests
            itself, before any route or auth middleware runs.
        EXPECTED: 2xx/204, with an Access-Control-Allow-Methods header present.
        SEVERITY: LOW
        """
        r = client.request(
            "OPTIONS",
            LOGIN,
            headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
        )
        assert 200 <= r.status_code < 300
        assert "access-control-allow-methods" in {k.lower() for k in r.headers.keys()}

    def test_cors_preflight_does_not_require_authentication(self, client):
        """
        CATEGORY: Configuration
        TITLE: OPTIONS preflight to a protected endpoint bypasses requireAuth
        OBJECTIVE: The cors() middleware is mounted before requireAuth and
            intercepts OPTIONS requests directly; confirm a browser's
            preflight to a protected route never gets a 401 (which would
            break every cross-origin authenticated call from the web app).
        EXPECTED: 2xx/204 on OPTIONS /api/auth/me with no Authorization header.
        SEVERITY: LOW
        """
        r = client.request(
            "OPTIONS", ME, headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"}
        )
        assert 200 <= r.status_code < 300


class TestErrorHandling:
    def test_unknown_route_returns_404_json(self, client):
        """
        CATEGORY: Configuration
        TITLE: Unmounted route returns a clean 404
        OBJECTIVE: Confirm requesting a path with no matching route returns
            Express's default 404 rather than crashing.
        EXPECTED: 404.
        SEVERITY: LOW
        """
        r = client.get("/api/this-route-does-not-exist")
        assert r.status_code == 404

    def test_error_response_never_contains_a_stack_trace(self, client):
        """
        CATEGORY: Configuration
        TITLE: Validation error responses don't leak stack traces or file paths
        OBJECTIVE: Trigger a routine 400 (invalid register payload) and
            confirm the JSON body contains no source file paths or "at "
            stack-frame markers.
        EXPECTED: No "    at " substring, no ".ts:" or ".js:" substring in
            the raw response body.
        SEVERITY: MEDIUM
        """
        r = client.post(REGISTER, json={"email": "not-an-email"})
        body_text = r.text
        assert "    at " not in body_text
        assert ".ts:" not in body_text
        assert "/backend/src/" not in body_text

    def test_malformed_json_body_error_does_not_leak_internals(self, client):
        """
        CATEGORY: Configuration
        TITLE: Body-parser JSON syntax error response stays generic (though wrongly a 500 -- see test_authentication.py finding)
        OBJECTIVE: Confirm Express's error handling for a JSON parse failure
            doesn't echo back internal file paths or dependency versions,
            independent of the separately-tracked status-code finding.
        EXPECTED: A response is returned (currently 500, see the dedicated
            finding test), and the response body contains no "node_modules" substring.
        SEVERITY: LOW
        """
        r = client.post(REGISTER, content=b"{bad json", headers={"Content-Type": "application/json"})
        assert "node_modules" not in r.text

    def test_health_endpoint_public_and_well_formed(self, client):
        """
        CATEGORY: Configuration
        TITLE: /health is public and returns the documented shape
        OBJECTIVE: Confirm the liveness endpoint needs no auth and returns
            status/service/timestamp, matching app.ts's handler.
        EXPECTED: 200, body has "status": "ok" and a "timestamp" field.
        SEVERITY: LOW
        """
        r = client.get(HEALTH)
        assert r.status_code == 200
        body = r.json()
        assert body.get("status") == "ok"
        assert "timestamp" in body


class TestCookieUsage:
    def test_register_never_sets_a_cookie(self, client):
        """
        CATEGORY: Configuration
        TITLE: Register response sets no Set-Cookie header
        OBJECTIVE: FitFuel is Bearer-token-only (no server-side sessions);
            confirm no cookie is ever issued, which would otherwise introduce
            CSRF surface the frontend/tests don't account for.
        EXPECTED: "set-cookie" absent from response headers.
        SEVERITY: LOW
        """
        import uuid

        r = client.post(
            REGISTER,
            json={"name": "Cookie Check", "email": f"cookie-{uuid.uuid4().hex[:8]}@backendtests.local", "password": "validpass1"},
        )
        assert "set-cookie" not in {k.lower() for k in r.headers.keys()}

    def test_login_never_sets_a_cookie(self, client, user_a):
        """
        CATEGORY: Configuration
        TITLE: Login response sets no Set-Cookie header
        OBJECTIVE: Same rationale as registration, for the login endpoint.
        EXPECTED: "set-cookie" absent from response headers.
        SEVERITY: LOW
        """
        r = client.post(LOGIN, json={"email": "irrelevant@backendtests.local", "password": "irrelevant"})
        assert "set-cookie" not in {k.lower() for k in r.headers.keys()}


class TestRateLimitingConfiguration:
    def test_no_rate_limit_headers_present_on_login(self, client):
        """
        CATEGORY: Configuration
        TITLE: [FINDING] No rate-limiting middleware is mounted
        OBJECTIVE: Neither express-rate-limit nor any equivalent appears in
            backend/package.json's dependencies, and app.ts mounts no
            rate-limiting middleware. Confirm the absence is real by checking
            for the headers such middleware would add.
        EXPECTED (documents current state): no X-RateLimit-* / RateLimit-*
            headers on repeated login attempts. See test_dast.py for the
            behavioral confirmation (rapid-fire attempts never 429).
        SEVERITY: MEDIUM
        """
        r = client.post(LOGIN, json={"email": "ratelimit-check@backendtests.local", "password": "wrong"})
        header_names = {k.lower() for k in r.headers.keys()}
        rate_limit_headers = {h for h in header_names if "ratelimit" in h}
        assert rate_limit_headers == set()


class TestBodyParsing:
    def test_wrong_content_type_with_json_body_does_not_crash(self, client):
        """
        CATEGORY: Configuration
        TITLE: Non-JSON Content-Type with a JSON-shaped body handled gracefully
        OBJECTIVE: express.json() only parses bodies whose Content-Type is
            application/json; confirm sending the same payload as
            text/plain doesn't crash the request (body simply won't be parsed
            as JSON, so validation should reject it cleanly).
        EXPECTED: 4xx, never 500.
        SEVERITY: LOW
        """
        r = client.post(
            REGISTER,
            content=json.dumps({"name": "X", "email": "x@backendtests.local", "password": "validpass1"}),
            headers={"Content-Type": "text/plain"},
        )
        assert r.status_code != 500

    def test_oversized_json_body_rejected_but_with_wrong_status_code(self, client):
        """
        CATEGORY: Configuration
        TITLE: [FINDING] Oversized request bodies return 500 instead of 413
        OBJECTIVE: Same root cause as the malformed-JSON finding in
            test_authentication.py: body-parser's PayloadTooLargeError
            carries `.status = 413`, but app.ts's central error handler
            discards it and always responds 500. Confirmed directly against
            the live server with a 200KB body (over the 100kb default limit).
        EXPECTED (documents confirmed, real behavior): 500 with a generic
            error body, where 413 would be the technically correct status.
            Same recommended fix as the malformed-JSON finding: honor
            err.status/err.statusCode in the central error handler.
        SEVERITY: LOW
        """
        oversized_notes = "A" * 200_000  # 200KB, well over the 100kb default
        r = client.post(
            REGISTER,
            json={"name": "X", "email": "oversized@backendtests.local", "password": "validpass1", "notes": oversized_notes},
        )
        assert r.status_code == 500


class TestMethodHandling:
    def test_unsupported_http_method_on_meals_returns_404(self, client):
        """
        CATEGORY: Configuration
        TITLE: DELETE on a GET-only route returns 404, not 500
        OBJECTIVE: Express routers 404 on a method with no matching handler
            registered for that path (there is no DELETE handler on /api/meals).
        EXPECTED: 404.
        SEVERITY: LOW
        """
        r = client.delete(f"{API_PREFIX}/meals")
        assert r.status_code == 404

    def test_unsupported_http_method_on_login_returns_404(self, client):
        """
        CATEGORY: Configuration
        TITLE: PUT on a POST-only route returns 404, not 500
        OBJECTIVE: Same rationale, for /api/auth/login (POST-only).
        EXPECTED: 404.
        SEVERITY: LOW
        """
        r = client.put(LOGIN, json={})
        assert r.status_code == 404
