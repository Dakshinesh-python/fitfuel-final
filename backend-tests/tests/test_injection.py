"""
Injection tests: fire attack-payload strings at fields that reach Prisma /
the filesystem / an outbound HTTP call with little or no format validation,
and confirm the app fails safely (parameterized queries hold, no shell is
invoked, no SSRF occurs) rather than fails open or crashes.

Deliberately does NOT fire SQLi payloads at fields already covered by format
validation (email, uuid) in test_input_validation.py -- those would just be
400'd by zod before reaching Prisma, which proves nothing new. Every payload
here targets a field the source code sends to Prisma/an LLM call as a raw,
unvalidated (or only length-validated) string.
"""
import uuid

import pytest

from config import API_PREFIX
from utils.payloads import (
    SQL_INJECTION_PAYLOADS,
    COMMAND_INJECTION_PAYLOADS,
    PATH_TRAVERSAL_PAYLOADS,
    XSS_PAYLOADS,
    SSRF_PAYLOADS,
    NOSQL_INJECTION_PAYLOADS,
)

REGISTER = f"{API_PREFIX}/auth/register"
CHAT = f"{API_PREFIX}/chat"
MEALS = f"{API_PREFIX}/meals"
PROGRESS = f"{API_PREFIX}/progress"


def _sqli_ids():
    return [f"sqli-{i}" for i in range(len(SQL_INJECTION_PAYLOADS))]


def _cmdi_ids():
    return [f"cmdi-{i}" for i in range(len(COMMAND_INJECTION_PAYLOADS))]


class TestSQLInjection:
    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS, ids=_sqli_ids())
    def test_sql_injection_payload_in_register_name_is_stored_as_literal(self, client, payload):
        """
        CATEGORY: Injection
        TITLE: SQL injection payload in registration name field
        OBJECTIVE: `name` has no format restriction beyond min(2) and is
            passed to prisma.user.create({data:{name,...}}), which Prisma
            parameterizes. Confirm the payload is accepted as inert literal
            data, not interpreted as SQL.
        EXPECTED: 201, response's user.name equals the payload verbatim
            (proves it was stored/echoed as data), and never a 500 (which
            would indicate a SQL syntax error reaching the DB driver).
        SEVERITY: HIGH
        """
        email = f"sqli-{uuid.uuid4().hex[:10]}@backendtests.local"
        r = client.post(REGISTER, json={"name": payload, "email": email, "password": "validpass1"})
        assert r.status_code != 500
        if r.status_code == 201:
            assert r.json()["user"]["name"] == payload

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS, ids=_sqli_ids())
    def test_sql_injection_payload_in_chat_message_handled_safely(self, client, user_a, payload):
        """
        CATEGORY: Injection
        TITLE: SQL injection payload in chat message field
        OBJECTIVE: The chat message never reaches Prisma directly (it goes to
            the LLM service, with the user's profile queried separately by
            userId), but confirm it doesn't crash the request pipeline.
        EXPECTED: 200, never 500.
        SEVERITY: MEDIUM
        """
        r = client.post(CHAT, json={"message": payload if payload else "x"}, headers=user_a["headers"])
        assert r.status_code in (200, 400)
        assert r.status_code != 500

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS, ids=_sqli_ids())
    def test_sql_injection_payload_in_cuisine_filter_does_not_bypass_filter(self, client, payload):
        """
        CATEGORY: Injection
        TITLE: [Security-relevant] SQL injection payload as a meal-catalog filter
        OBJECTIVE: `cuisine` from GET /api/meals?cuisine=... goes straight into
            Prisma's `where` clause with no format validation. This is the
            single highest-value injection check in the suite: if the
            underlying query were ever built with raw string concatenation
            instead of Prisma's parameterized query builder, a payload like
            `' OR '1'='1` would make the filter match every row instead of
            zero rows.
        EXPECTED: 200, and the result set is empty (or at least not the full,
            unfiltered catalog) -- proving the payload was treated as a
            literal (and non-matching) cuisine name. Never a 500.
        SEVERITY: CRITICAL
        """
        baseline = client.get(MEALS)
        r = client.get(MEALS, params={"cuisine": payload})
        assert r.status_code != 500
        if r.status_code == 200:
            injected_count = len(r.json()["meals"])
            baseline_count = len(baseline.json()["meals"])
            assert injected_count == 0 or injected_count < baseline_count, (
                f"cuisine={payload!r} returned {injected_count} meals (baseline unfiltered: "
                f"{baseline_count}) -- filter may not be parameterized correctly"
            )


class TestCommandInjection:
    @pytest.mark.parametrize("payload", COMMAND_INJECTION_PAYLOADS, ids=_cmdi_ids())
    def test_command_injection_payload_in_register_name(self, client, payload):
        """
        CATEGORY: Injection
        TITLE: Shell metacharacters in registration name
        OBJECTIVE: Nothing in the register path shells out, but confirm shell
            metacharacters in free-text fields don't trigger any unexpected
            behavior (e.g. a logging library interpreting them).
        EXPECTED: 201 or 400 (if trimmed length < 2), never 500.
        SEVERITY: LOW
        """
        email = f"cmdi-{uuid.uuid4().hex[:10]}@backendtests.local"
        r = client.post(REGISTER, json={"name": payload, "email": email, "password": "validpass1"})
        assert r.status_code != 500

    @pytest.mark.parametrize("payload", COMMAND_INJECTION_PAYLOADS, ids=_cmdi_ids())
    def test_command_injection_payload_in_chat_message(self, client, user_a, payload):
        """
        CATEGORY: Injection
        TITLE: Shell metacharacters in chat message
        OBJECTIVE: Same rationale as above, for the chat endpoint.
        EXPECTED: 200 or 400, never 500.
        SEVERITY: LOW
        """
        msg = payload if payload.strip() else "x"
        r = client.post(CHAT, json={"message": msg[:500]}, headers=user_a["headers"])
        assert r.status_code != 500

    @pytest.mark.parametrize("payload", COMMAND_INJECTION_PAYLOADS, ids=_cmdi_ids())
    def test_command_injection_payload_in_progress_notes(self, client, user_a, payload):
        """
        CATEGORY: Injection
        TITLE: Shell metacharacters in progress-log notes
        OBJECTIVE: Same rationale as above, for the free-text notes field.
        EXPECTED: 201, never 500.
        SEVERITY: LOW
        """
        r = client.post(PROGRESS, json={"notes": payload}, headers=user_a["headers"])
        assert r.status_code == 201


class TestPathTraversal:
    @pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS, ids=[f"traversal-{i}" for i in range(len(PATH_TRAVERSAL_PAYLOADS))])
    def test_path_traversal_payload_as_meal_id_never_leaks_files(self, client, payload):
        """
        CATEGORY: Injection
        TITLE: Path traversal payload as meal :id path parameter
        OBJECTIVE: GET /api/meals/:id passes req.params.id straight to
            Prisma's findUnique -- there is no filesystem access on this path
            at all, so traversal payloads should be inert. This test exists
            to positively confirm that (not because the code pattern
            suggested a risk).
        EXPECTED: 404 (or the client-side URL normalization routes it
            elsewhere entirely, also fine), and the response body never
            contains filesystem content markers like "root:x:0:0".
        SEVERITY: LOW
        """
        r = client.get(f"{MEALS}/{payload}")
        assert r.status_code != 500
        assert "root:x:0:0" not in r.text
        assert "[extensions]" not in r.text  # win.ini marker


class TestXSSPayloads:
    @pytest.mark.parametrize("payload", XSS_PAYLOADS, ids=[f"xss-{i}" for i in range(len(XSS_PAYLOADS))])
    def test_xss_payload_in_register_name_returned_as_inert_json_string(self, client, payload):
        """
        CATEGORY: Injection
        TITLE: XSS payload in registration name stays inert JSON data
        OBJECTIVE: FitFuel's backend is a pure JSON API -- it never renders
            HTML server-side, so HTML-escaping the name field would actually
            be *wrong* (it's the web frontend's job to escape on render).
            Confirm the API returns it as plain JSON without executing it or
            changing Content-Type.
        EXPECTED: 201, Content-Type stays application/json, name field equals
            the payload verbatim.
        SEVERITY: LOW
        """
        email = f"xss-{uuid.uuid4().hex[:10]}@backendtests.local"
        r = client.post(REGISTER, json={"name": payload, "email": email, "password": "validpass1"})
        assert r.status_code == 201
        assert "application/json" in r.headers.get("content-type", "")
        assert r.json()["user"]["name"] == payload

    @pytest.mark.parametrize("payload", XSS_PAYLOADS, ids=[f"xss-{i}" for i in range(len(XSS_PAYLOADS))])
    def test_xss_payload_in_chat_message_returns_inert_json(self, client, user_a, payload):
        """
        CATEGORY: Injection
        TITLE: XSS payload in chat message stays inert JSON data
        OBJECTIVE: Same rationale, for the chat endpoint.
        EXPECTED: 200, Content-Type stays application/json.
        SEVERITY: LOW
        """
        r = client.post(CHAT, json={"message": payload}, headers=user_a["headers"])
        assert r.status_code == 200
        assert "application/json" in r.headers.get("content-type", "")


class TestSSRFAttempts:
    @pytest.mark.parametrize("payload", SSRF_PAYLOADS, ids=[f"ssrf-{i}" for i in range(len(SSRF_PAYLOADS))])
    def test_ssrf_style_payload_in_chat_message_triggers_no_outbound_fetch(self, client, user_a, payload):
        """
        CATEGORY: Injection
        TITLE: SSRF-style URL in chat message
        OBJECTIVE: The only outbound call chat can trigger is to the hardcoded
            Groq endpoint in aiExplainerService.ts -- the user's message text
            is sent as an LLM prompt, never used to build a URL. Confirm
            passing URL-shaped payloads doesn't change that.
        EXPECTED: 200 in a reasonable time (no evidence of the server itself
            trying to connect to the target host, which would show up as a
            multi-second timeout-shaped delay for the internal metadata IP).
        SEVERITY: LOW
        """
        import time as _time

        start = _time.monotonic()
        r = client.post(CHAT, json={"message": f"Tell me about {payload}"}, headers=user_a["headers"])
        elapsed = _time.monotonic() - start
        assert r.status_code == 200
        assert elapsed < 10, f"Unexpectedly slow response ({elapsed:.1f}s) -- possible outbound connection attempt"


class TestNoSQLStyleOperatorInjection:
    @pytest.mark.parametrize("payload", NOSQL_INJECTION_PAYLOADS, ids=[f"nosql-{i}" for i in range(len(NOSQL_INJECTION_PAYLOADS))])
    def test_operator_object_as_email_rejected_by_type_validation(self, client, payload):
        """
        CATEGORY: Injection
        TITLE: MongoDB-style operator object rejected as an email value
        OBJECTIVE: Postgres/Prisma isn't a document store, so classic NoSQL
            operator injection doesn't apply directly -- but confirm zod's
            z.string().email() correctly rejects a JSON *object* where a
            string is expected, rather than something coercing it.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(REGISTER, json={"name": "NoSQL Test", "email": payload, "password": "validpass1"})
        assert r.status_code == 400
