"""Shared, reusable test data sets for parametrized tests."""

MALFORMED_EMAILS = [
    "plainaddress",
    "@missing-local.com",
    "missing-domain@",
    "no-tld@example",
    "two..dots@example.com",
    "trailing-dot.@example.com",
    ".leading-dot@example.com",
    "spaces in@email.com",
    " leading-space@example.com",
    "trailing-space@example.com ",
    "double@@at.com",
    "bad,comma@example.com",
    "semicolon;in@local.com",
    "colon_in@local.com",
    "under_score()@example.com",
    "newline\nin@example.com",
    "quoted_name_\"@example.com",
]

VALID_LOOKING_EMAILS = [
    "user@example.com",
    "first.last@example.co.uk",
    "user+tag@example.com",
    "user_name@example-domain.com",
    "u@e.io",
]

WEAK_PASSWORDS = [
    "",
    "1234567",       # 7 chars, below the 8-char minLength
    "short",
    "       ",       # whitespace only
    "a" * 6,
]

BOUNDARY_STRINGS = {
    "empty": "",
    "single_char": "a",
    "very_long": "A" * 200,
    "unicode_name": "名前",
    "emoji": "🙂🥗💪",
    "sql_injection": "'; DROP TABLE users; --",
    "script_tag": "<script>alert(1)</script>",
    "html_entities": "&lt;b&gt;bold&lt;/b&gt;",
    "leading_trailing_space": "  padded value  ",
    "apostrophe_name": "O'Brien-Smith",
}

INVALID_NUMERIC_INPUTS = [
    "-1",
    "0",
    "abc",
    "1.5.5",
    "99999999999999",
    "-999",
]

VALID_NUMERIC_INPUTS = ["50", "70.5", "120", "1"]

RESPONSIVE_BREAKPOINTS = [
    ("mobile-small", 320, 640),
    ("mobile", 375, 667),
    ("mobile-large", 414, 896),
    ("tablet-boundary-767", 767, 1024),
    ("tablet-boundary-768", 768, 1024),
    ("tablet", 834, 1112),
    ("desktop-boundary-1023", 1023, 800),
    ("desktop-boundary-1024", 1024, 800),
    ("desktop", 1440, 900),
    ("desktop-large", 1920, 1080),
]

INVALID_ROUTES = [
    "does-not-exist",
    "dashboard/extra",
    "DASHBOARD",
    "login/",
    "%2e%2e",
    "admin",
]

GUEST_FLAG_LIKE_VALUES = ["true", "TRUE", "True", " true", "true ", "1", "yes", "on", ""]
