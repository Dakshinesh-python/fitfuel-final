"""
Payload libraries shared across test_injection.py, test_dast.py, and
test_input_validation.py. Centralized so each list is defined once and
reused across endpoints via parametrization, and so severity/rationale
stays next to the payload instead of scattered across test files.
"""

# SQL-injection-style strings. Prisma's query builder parameterizes every
# value it's given, so the *expected* result for all of these is "rejected
# by validation (400) or treated as inert literal data (200/404) -- never
# a 500 and never a syntax-error leak." A 500 here would indicate raw SQL
# string-building somewhere, which the codebase does not appear to do.
SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1--",
    "'; DROP TABLE \"User\";--",
    "' UNION SELECT NULL,NULL,NULL--",
    "admin'--",
    "1' AND '1'='1",
    "') OR ('1'='1",
    "'; SELECT pg_sleep(5);--",
    "' OR 'x'='x",
    "1;SELECT * FROM \"User\"",
    "\" OR \"\"=\"",
    "' OR SLEEP(5)='0",
    "%27%20OR%201%3D1",  # URL-encoded ' OR 1=1
    "'||(SELECT 1)||'",
    "1' ORDER BY 100--",
]

# NoSQL/operator-injection style payloads. Postgres/Prisma isn't a NoSQL
# store, but these also double as "does the API blindly JSON.parse and pass
# objects through to a where-clause" checks.
NOSQL_INJECTION_PAYLOADS = [
    {"$gt": ""},
    {"$ne": None},
    {"$regex": ".*"},
    {"email": {"$ne": None}},
]

# Command-injection style strings for free-text fields (name, notes, chat
# message). Nothing in the backend shells out, so expected result is
# "treated as inert string data" -- a check that stays true, not a
# vulnerability we expect to find.
COMMAND_INJECTION_PAYLOADS = [
    "; ls -la",
    "$(whoami)",
    "`id`",
    "| cat /etc/passwd",
    "&& curl http://example.com",
    "test\nrm -rf /",
]

# Path traversal payloads for the /api/meals/:id path parameter.
PATH_TRAVERSAL_PAYLOADS = [
    "../../etc/passwd",
    "..%2f..%2fetc%2fpasswd",
    "....//....//etc/passwd",
    "%2e%2e%2fetc%2fpasswd",
    "..\\..\\windows\\win.ini",
]

# SSRF-style payloads for any field that could plausibly be used to build
# an outbound URL. FitFuel's only outbound HTTP call is the hardcoded Groq
# endpoint in aiExplainerService.ts, so these are attempted against the
# chat message body as a "does user input ever reach an outbound fetch"
# check rather than an expected-to-succeed attack.
SSRF_PAYLOADS = [
    "http://169.254.169.254/latest/meta-data/",
    "http://localhost:4000/api/auth/me",
    "file:///etc/passwd",
    "http://[::1]:22",
]

# Reflected-XSS-style payloads. FitFuel is a JSON API (no server-rendered
# HTML), so the expected result is "returned as an inert JSON string
# value, Content-Type stays application/json" -- not "sanitized/stripped."
XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "\"><svg onload=alert(1)>",
    "javascript:alert(1)",
    "<iframe src=javascript:alert(1)>",
]

# Malformed / boundary email strings for register + login validation tests.
# Each of these was checked against the actual zod schema (z.string().email())
# in isolation (`node -e "z.string().email().safeParse(...)"`) before being
# added here, so the "should be rejected" expectation is verified fact, not
# an assumption carried over from the template.
MALFORMED_EMAILS = [
    "not-an-email",
    "missing-domain@",
    "@missing-local.com",
    "double@@at.com",
    "trailing-dot.@example.com",
    ".leading-dot@example.com",
    "spaces in@email.com",
    "no-tld@example",
    "under_score()@example.com",
    "semicolon;in@local.com",
    "",
]

# NOT malformed by zod's email() regex (verified: this actually parses as
# VALID) -- used by test_input_validation.py to document the missing
# max-length constraint on the email field, rather than mis-filed under
# MALFORMED_EMAILS where it would produce a false test failure.
OVERSIZED_BUT_ZOD_VALID_EMAIL = "a" * 300 + "@example.com"

# Oversized / boundary strings reused across several input-validation tests.
def long_string(n: int) -> str:
    return "A" * n


UNICODE_STRINGS = [
    "名前",  # Japanese
    "Имя",  # Cyrillic
    "🏋️‍♂️🥗",  # emoji
    "O'Brien-Smith",
    "  leading and trailing  ",
]
