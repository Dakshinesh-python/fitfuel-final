"""
Authentication tests: POST /api/auth/register, POST /api/auth/login,
GET /api/auth/me, PATCH /api/auth/profile, PATCH /api/auth/password.

Confirmed against backend/src/routes/auth.routes.ts and
backend/src/middleware/auth.ts.
"""
import uuid

import jwt
import pytest

from config import API_PREFIX, DEFAULT_JWT_SECRET_FALLBACK
from utils.payloads import MALFORMED_EMAILS, UNICODE_STRINGS, long_string

REGISTER = f"{API_PREFIX}/auth/register"
LOGIN = f"{API_PREFIX}/auth/login"
ME = f"{API_PREFIX}/auth/me"
PROFILE = f"{API_PREFIX}/auth/profile"
PASSWORD = f"{API_PREFIX}/auth/password"


def _uniq(prefix="authtest"):
    return f"{prefix}-{uuid.uuid4().hex[:10]}@backendtests.local"


def _valid_payload(**overrides):
    payload = {
        "name": "Auth Test User",
        "email": _uniq(),
        "password": "ValidPass123",
    }
    payload.update(overrides)
    return payload


class TestRegistration:
    def test_register_valid_user_returns_201(self, client):
        """
        CATEGORY: Authentication
        TITLE: Valid registration succeeds
        OBJECTIVE: Confirm a well-formed registration request creates an account.
        EXPECTED: 201, response includes token and user object.
        SEVERITY: HIGH
        """
        r = client.post(REGISTER, json=_valid_payload())
        assert r.status_code == 201
        body = r.json()
        assert "token" in body and body["token"]
        assert body["user"]["email"]

    def test_register_duplicate_email_returns_409(self, client):
        """
        CATEGORY: Authentication
        TITLE: Duplicate email rejected
        OBJECTIVE: Confirm registering twice with the same email is blocked.
        EXPECTED: Second call returns 409 with an error message.
        SEVERITY: HIGH
        """
        payload = _valid_payload()
        first = client.post(REGISTER, json=payload)
        assert first.status_code == 201
        second = client.post(REGISTER, json=payload)
        assert second.status_code == 409
        assert "error" in second.json()

    @pytest.mark.parametrize("bad_email", MALFORMED_EMAILS, ids=[f"email-{i}" for i in range(len(MALFORMED_EMAILS))])
    def test_register_rejects_malformed_email(self, client, bad_email):
        """
        CATEGORY: Authentication
        TITLE: Malformed email rejected at registration
        OBJECTIVE: Confirm zod email validation rejects non-RFC email strings.
        EXPECTED: 400 with a validation error, never a 500.
        SEVERITY: MEDIUM
        """
        r = client.post(REGISTER, json=_valid_payload(email=bad_email))
        assert r.status_code == 400, f"payload {bad_email!r} got {r.status_code}: {r.text}"

    @pytest.mark.parametrize("short_pw", ["", "a", "ab", "abcd", "abcde"])
    def test_register_rejects_short_password(self, client, short_pw):
        """
        CATEGORY: Authentication
        TITLE: Sub-minimum-length password rejected
        OBJECTIVE: Confirm the 6-character password minimum (zod min(6)) is enforced.
        EXPECTED: 400 for every password shorter than 6 characters.
        SEVERITY: MEDIUM
        """
        r = client.post(REGISTER, json=_valid_payload(password=short_pw))
        assert r.status_code == 400

    def test_register_accepts_password_at_min_boundary(self, client):
        """
        CATEGORY: Authentication
        TITLE: Exactly-6-character password accepted
        OBJECTIVE: Confirm the boundary value itself (not just below it) is accepted.
        EXPECTED: 201 - min(6) means 6 is valid, not just >6.
        SEVERITY: LOW
        """
        r = client.post(REGISTER, json=_valid_payload(password="abcdef"))
        assert r.status_code == 201

    @pytest.mark.parametrize("field", ["name", "email", "password"])
    def test_register_missing_required_field(self, client, field):
        """
        CATEGORY: Authentication
        TITLE: Missing required field rejected
        OBJECTIVE: Confirm each required field is actually enforced by the schema.
        EXPECTED: 400 when the field is absent entirely.
        SEVERITY: MEDIUM
        """
        payload = _valid_payload()
        del payload[field]
        r = client.post(REGISTER, json=payload)
        assert r.status_code == 400

    def test_register_ignores_unexpected_privileged_fields(self, client):
        """
        CATEGORY: Authentication
        TITLE: Mass-assignment of unexpected fields is ignored
        OBJECTIVE: Confirm a caller cannot set fields like id/isAdmin/passwordHash
            directly through registration (zod schema only picks known keys).
        EXPECTED: 201, and the forged fields have no effect (account is a normal user).
        SEVERITY: HIGH
        """
        payload = _valid_payload(**{"id": "forged-id", "isAdmin": True, "passwordHash": "x"})
        r = client.post(REGISTER, json=payload)
        assert r.status_code == 201
        body = r.json()
        assert body["user"]["id"] != "forged-id"

    def test_register_response_never_includes_password_hash(self, client):
        """
        CATEGORY: Authentication
        TITLE: passwordHash never leaves the API
        OBJECTIVE: Confirm the register response's user object excludes passwordHash.
        EXPECTED: "passwordHash" key absent from response body.
        SEVERITY: CRITICAL
        """
        r = client.post(REGISTER, json=_valid_payload())
        assert r.status_code == 201
        assert "passwordHash" not in r.json()["user"]

    def test_register_extremely_long_password_does_not_500(self, client):
        """
        CATEGORY: Authentication
        TITLE: Long password does not crash bcrypt hashing
        OBJECTIVE: bcryptjs silently truncates at 72 bytes rather than raising, unlike
            some bcrypt bindings that throw past 72 bytes. Confirm no uncaught 500.
        EXPECTED: 201 (bcryptjs truncates rather than erroring); never a 500.
        SEVERITY: MEDIUM
        """
        r = client.post(REGISTER, json=_valid_payload(password=long_string(200)))
        assert r.status_code in (201, 400)
        assert r.status_code != 500

    @pytest.mark.parametrize("name", UNICODE_STRINGS, ids=[f"unicode-{i}" for i in range(len(UNICODE_STRINGS))])
    def test_register_unicode_and_special_names_accepted(self, client, name):
        """
        CATEGORY: Authentication
        TITLE: Unicode / special-character names accepted
        OBJECTIVE: Confirm names with non-ASCII characters, apostrophes, or
            leading/trailing whitespace don't break registration. Verified
            against the actual zod schema (z.string().min(2)) beforehand --
            every string in this list has length >= 2, so 201 is the only
            correct outcome, not just a plausible one.
        EXPECTED: 201.
        SEVERITY: LOW
        """
        r = client.post(REGISTER, json=_valid_payload(name=name))
        assert r.status_code == 201

    def test_register_single_character_name_rejected(self, client):
        """
        CATEGORY: Authentication
        TITLE: Single-character name rejected
        OBJECTIVE: Confirm zod's name min(2) boundary is enforced.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(REGISTER, json=_valid_payload(name="A"))
        assert r.status_code == 400

    def test_register_negative_age_rejected(self, client):
        """
        CATEGORY: Authentication
        TITLE: Negative age rejected
        OBJECTIVE: Confirm zod's age positive-int constraint is enforced.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(REGISTER, json=_valid_payload(age=-5))
        assert r.status_code == 400

    def test_register_invalid_gender_enum_rejected(self, client):
        """
        CATEGORY: Authentication
        TITLE: Invalid gender enum value rejected
        OBJECTIVE: Confirm gender is restricted to MALE/FEMALE/OTHER.
        EXPECTED: 400 for an out-of-enum value.
        SEVERITY: LOW
        """
        r = client.post(REGISTER, json=_valid_payload(gender="ROBOT"))
        assert r.status_code == 400

    def test_passwords_sharing_a_72_byte_prefix_are_treated_as_identical(self, client):
        """
        CATEGORY: Authentication
        TITLE: [FINDING] bcrypt 72-byte truncation allows password-prefix collisions
        OBJECTIVE: bcrypt (and bcryptjs specifically, confirmed via direct
            library test: bcrypt.compare returned true for two different
            >72-byte strings sharing only their first 72 bytes) silently
            truncates input at 72 bytes rather than hashing the full string.
            Register with a long password, then attempt login using a
            different password that shares the same first-72-byte prefix.
        EXPECTED (documents current, verified behavior): login SUCCEEDS with
            the differing-tail password, because both hash identically. This
            is expected bcrypt behavior, not an application bug, but it means
            passwords longer than 72 bytes provide no additional entropy
            beyond the first 72 bytes -- worth surfacing since neither the
            frontend nor the API enforces a max length that would prevent a
            user from unknowingly relying on those extra bytes.
        SEVERITY: MEDIUM
        """
        prefix = "P" * 72
        r = client.post(REGISTER, json=_valid_payload(password=prefix + "-original-tail"))
        assert r.status_code == 201
        email = r.json()["user"]["email"]

        login = client.post(LOGIN, json={"email": email, "password": prefix + "-COMPLETELY-DIFFERENT-TAIL"})
        assert login.status_code == 200, (
            "If this now fails, bcryptjs's truncation behavior has changed upstream -- "
            "re-verify with `bcrypt.compare()` directly before treating this as a regression."
        )

    def test_register_non_json_body_rejected_without_crashing_the_process(self, client):
        """
        CATEGORY: Authentication
        TITLE: [FINDING] Malformed JSON body returns 500 instead of 400
        OBJECTIVE: Confirmed directly against the live server: app.ts's
            central error handler (`app.use((err, _req, res, _next) => {
            res.status(500).json(...) })`) unconditionally returns 500 for
            ANY error reaching it, discarding the actual error's status code.
            express.json()'s body-parser throws a SyntaxError with
            `.status/.statusCode = 400` for malformed JSON, but that 400 is
            thrown away and replaced with a generic 500.
        EXPECTED (documents confirmed, real behavior): 500 with
            {"error": "Internal server error"} for invalid JSON syntax. This
            should be a 400 -- the request is a client error (bad syntax),
            not a server fault. Recommended fix: check `err.status ??
            err.statusCode ?? 500` in the central handler instead of always
            using 500. Low functional impact (the request still fails
            correctly either way) but pollutes 5xx-based monitoring/alerting
            with what are actually client-side mistakes.
        SEVERITY: MEDIUM
        """
        r = client.post(REGISTER, content=b"{not valid json", headers={"Content-Type": "application/json"})
        assert r.status_code == 500
        assert r.json() == {"error": "Internal server error"}

    def test_register_non_json_body_never_crashes_the_server_process(self, client):
        """
        CATEGORY: Authentication
        TITLE: Malformed JSON body does not crash the Node process
        OBJECTIVE: Regardless of the status-code finding above, confirm the
            server itself survives a malformed-JSON request and continues
            serving subsequent requests normally.
        EXPECTED: /health still returns 200 immediately afterwards.
        SEVERITY: HIGH
        """
        client.post(REGISTER, content=b"{not valid json", headers={"Content-Type": "application/json"})
        assert client.get("/health").status_code == 200


class TestLogin:
    @pytest.fixture()
    def registered_user(self, client):
        payload = _valid_payload()
        r = client.post(REGISTER, json=payload)
        assert r.status_code == 201
        return payload

    def test_login_valid_credentials_returns_token(self, client, registered_user):
        """
        CATEGORY: Authentication
        TITLE: Correct credentials return a token
        OBJECTIVE: Confirm login succeeds for a just-registered account.
        EXPECTED: 200, response includes token + user.
        SEVERITY: HIGH
        """
        r = client.post(LOGIN, json={"email": registered_user["email"], "password": registered_user["password"]})
        assert r.status_code == 200
        assert r.json()["token"]

    def test_login_wrong_password_returns_401(self, client, registered_user):
        """
        CATEGORY: Authentication
        TITLE: Wrong password rejected
        OBJECTIVE: Confirm an incorrect password does not authenticate.
        EXPECTED: 401.
        SEVERITY: HIGH
        """
        r = client.post(LOGIN, json={"email": registered_user["email"], "password": "wrong-password"})
        assert r.status_code == 401

    def test_login_unknown_email_returns_401(self, client):
        """
        CATEGORY: Authentication
        TITLE: Unknown email rejected
        OBJECTIVE: Confirm a non-existent account also returns 401 (not 404).
        EXPECTED: 401 -- 404 here would itself be an info-leak (see also
            test_dast.py::test_login_timing_does_not_reveal_account_existence).
        SEVERITY: HIGH
        """
        r = client.post(LOGIN, json={"email": _uniq("nobody"), "password": "whatever123"})
        assert r.status_code == 401

    def test_login_error_message_identical_for_wrong_password_and_unknown_email(self, client, registered_user):
        """
        CATEGORY: Authentication
        TITLE: Login error message does not leak account existence
        OBJECTIVE: Confirm "wrong password" and "unknown email" return the exact
            same error text, so the message body can't be used to enumerate
            registered accounts.
        EXPECTED: Both cases return {"error": "Invalid credentials"}.
        SEVERITY: MEDIUM
        """
        wrong_pw = client.post(LOGIN, json={"email": registered_user["email"], "password": "wrong-password"})
        unknown = client.post(LOGIN, json={"email": _uniq("nobody"), "password": "whatever123"})
        assert wrong_pw.json().get("error") == unknown.json().get("error")

    def test_login_missing_password_returns_400(self, client, registered_user):
        """
        CATEGORY: Authentication
        TITLE: Missing password field rejected
        OBJECTIVE: Confirm the login schema requires a password field.
        EXPECTED: 400.
        SEVERITY: MEDIUM
        """
        r = client.post(LOGIN, json={"email": registered_user["email"]})
        assert r.status_code == 400

    def test_login_missing_email_returns_400(self, client):
        """
        CATEGORY: Authentication
        TITLE: Missing email field rejected
        OBJECTIVE: Confirm the login schema requires an email field.
        EXPECTED: 400.
        SEVERITY: MEDIUM
        """
        r = client.post(LOGIN, json={"password": "whatever123"})
        assert r.status_code == 400

    def test_login_malformed_email_format_returns_400(self, client):
        """
        CATEGORY: Authentication
        TITLE: Malformed email at login rejected before a DB lookup
        OBJECTIVE: Confirm zod validates email shape on login too, not just register.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(LOGIN, json={"email": "not-an-email", "password": "whatever123"})
        assert r.status_code == 400

    def test_login_response_token_has_valid_jwt_structure(self, client, registered_user):
        """
        CATEGORY: Authentication
        TITLE: Issued token is a well-formed JWT
        OBJECTIVE: Confirm the token has a 3-part header.payload.signature structure
            and an unverified payload containing a userId claim.
        EXPECTED: Token splits into exactly 3 dot-separated segments; decoded
            payload (without verification) contains "userId" and "exp".
        SEVERITY: LOW
        """
        r = client.post(LOGIN, json={"email": registered_user["email"], "password": registered_user["password"]})
        token = r.json()["token"]
        assert token.count(".") == 2
        payload = jwt.decode(token, options={"verify_signature": False})
        assert "userId" in payload
        assert "exp" in payload

    def test_login_response_never_includes_password_hash(self, client, registered_user):
        """
        CATEGORY: Authentication
        TITLE: passwordHash never leaves the API on login either
        OBJECTIVE: Same check as registration, for the login response.
        EXPECTED: "passwordHash" absent from the user object.
        SEVERITY: CRITICAL
        """
        r = client.post(LOGIN, json={"email": registered_user["email"], "password": registered_user["password"]})
        assert "passwordHash" not in r.json()["user"]

    def test_login_email_is_case_sensitive_or_documented_as_such(self, client, registered_user):
        """
        CATEGORY: Authentication
        TITLE: Email case-sensitivity behavior is consistent
        OBJECTIVE: Prisma's default @unique on String is case-sensitive in Postgres.
            Confirm login with a differently-cased email behaves predictably
            (fails cleanly with 401, not a 500) rather than silently matching.
        EXPECTED: 401 or 200, but never 500 -- and the result should match
            whatever register-time uniqueness enforces.
        SEVERITY: LOW
        """
        upper_email = registered_user["email"].upper()
        r = client.post(LOGIN, json={"email": upper_email, "password": registered_user["password"]})
        assert r.status_code in (200, 401)


class TestSessionAndProfile:
    def test_me_requires_auth_returns_401_without_header(self, client):
        """
        CATEGORY: Authentication
        TITLE: /me rejects requests with no Authorization header
        OBJECTIVE: Confirm requireAuth middleware blocks unauthenticated access.
        EXPECTED: 401.
        SEVERITY: CRITICAL
        """
        r = client.get(ME)
        assert r.status_code == 401

    @pytest.mark.parametrize(
        "header_value",
        ["NotBearer sometoken", "Bearer", "", "bearer lowercase-scheme-token", "Basic dXNlcjpwYXNz"],
        ids=["wrong-scheme", "bearer-no-token", "empty", "lowercase-scheme", "basic-auth"],
    )
    def test_me_rejects_malformed_authorization_header(self, client, header_value):
        """
        CATEGORY: Authentication
        TITLE: Malformed Authorization header formats rejected
        OBJECTIVE: Confirm only a correctly-cased "Bearer <token>" header is accepted.
        EXPECTED: 401 for every malformed variant.
        SEVERITY: MEDIUM
        """
        r = client.get(ME, headers={"Authorization": header_value})
        assert r.status_code == 401

    def test_me_rejects_garbage_token(self, client):
        """
        CATEGORY: Authentication
        TITLE: Syntactically invalid token rejected
        OBJECTIVE: Confirm a random non-JWT string in the Bearer header is rejected.
        EXPECTED: 401.
        SEVERITY: HIGH
        """
        r = client.get(ME, headers={"Authorization": "Bearer not-a-real-jwt-token"})
        assert r.status_code == 401

    def test_me_rejects_token_signed_with_wrong_secret(self, client):
        """
        CATEGORY: Authentication
        TITLE: Token forged with an incorrect secret is rejected
        OBJECTIVE: Confirm jwt.verify actually checks the signature, not just shape.
        EXPECTED: 401 -- a token with valid structure but wrong signature must fail.
        SEVERITY: CRITICAL
        """
        forged = jwt.encode({"userId": "some-user-id"}, "totally-wrong-secret", algorithm="HS256")
        r = client.get(ME, headers={"Authorization": f"Bearer {forged}"})
        assert r.status_code == 401

    def test_me_rejects_expired_token(self, client):
        """
        CATEGORY: Authentication
        TITLE: Expired token rejected
        OBJECTIVE: Confirm the exp claim is enforced. Signed with the source-code
            default fallback secret (dev-secret-change-me) since the black-box
            test cannot know a real deployment's JWT_SECRET; if this fails to
            reproduce against a deployment with a real secret configured, that
            confirms the fallback is NOT in effect there (the desired state).
        EXPECTED: 401 for an already-expired exp claim, when the fallback secret
            is in effect. See findings.xlsx for the related default-secret finding.
        SEVERITY: MEDIUM
        """
        import time as _time
        expired = jwt.encode(
            {"userId": "some-user-id", "iat": int(_time.time()) - 1000, "exp": int(_time.time()) - 500},
            DEFAULT_JWT_SECRET_FALLBACK,
            algorithm="HS256",
        )
        r = client.get(ME, headers={"Authorization": f"Bearer {expired}"})
        assert r.status_code == 401

    def test_me_accepts_valid_token_and_returns_own_user(self, client, user_a):
        """
        CATEGORY: Authentication
        TITLE: Valid token returns the correct user
        OBJECTIVE: Confirm /me returns the profile matching the token's owner.
        EXPECTED: 200, returned user.id matches the id from registration.
        SEVERITY: HIGH
        """
        r = client.get(ME, headers=user_a["headers"])
        assert r.status_code == 200
        assert r.json()["user"]["id"] == user_a["id"]

    def test_profile_update_requires_auth(self, client):
        """
        CATEGORY: Authentication
        TITLE: Profile update requires authentication
        OBJECTIVE: Confirm PATCH /api/auth/profile is behind requireAuth.
        EXPECTED: 401 without a token.
        SEVERITY: HIGH
        """
        r = client.patch(PROFILE, json={"name": "New Name"})
        assert r.status_code == 401

    def test_profile_update_valid_name_succeeds(self, client, user_a):
        """
        CATEGORY: Authentication
        TITLE: Valid profile update succeeds
        OBJECTIVE: Confirm an authenticated user can update their display name.
        EXPECTED: 200, response reflects the new name.
        SEVERITY: MEDIUM
        """
        r = client.patch(PROFILE, json={"name": "Updated QA Name"}, headers=user_a["headers"])
        assert r.status_code == 200
        assert r.json()["user"]["name"] == "Updated QA Name"

    def test_profile_update_rejects_short_name(self, client, user_a):
        """
        CATEGORY: Authentication
        TITLE: Profile update enforces name length
        OBJECTIVE: Confirm the same min(2) rule applies on update as on register.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.patch(PROFILE, json={"name": "A"}, headers=user_a["headers"])
        assert r.status_code == 400

    def test_password_change_requires_auth(self, client):
        """
        CATEGORY: Authentication
        TITLE: Password change requires authentication
        OBJECTIVE: Confirm PATCH /api/auth/password is behind requireAuth.
        EXPECTED: 401 without a token.
        SEVERITY: HIGH
        """
        r = client.patch(PASSWORD, json={"currentPassword": "x", "newPassword": "newpass123"})
        assert r.status_code == 401

    def test_password_change_wrong_current_password_rejected(self, client, user_a):
        """
        CATEGORY: Authentication
        TITLE: Password change verifies the current password
        OBJECTIVE: Confirm a caller cannot change the password without proving
            they know the current one, even while holding a valid token.
        EXPECTED: 401 when currentPassword is wrong.
        SEVERITY: CRITICAL
        """
        r = client.patch(
            PASSWORD,
            json={"currentPassword": "definitely-wrong", "newPassword": "newpass123"},
            headers=user_a["headers"],
        )
        assert r.status_code == 401

    def test_password_change_new_password_too_short_rejected(self, client, user_b):
        """
        CATEGORY: Authentication
        TITLE: New password enforces its own (stricter) minimum length
        OBJECTIVE: changePasswordSchema requires newPassword min(8), one character
            stricter than registration's min(6) -- confirm the stricter bound wins.
        EXPECTED: 400 for a 6-character new password (valid for register, invalid here).
        SEVERITY: MEDIUM
        """
        from config import TEST_USER_B

        r = client.patch(
            PASSWORD,
            json={"currentPassword": TEST_USER_B["password"], "newPassword": "abcdef"},
            headers=user_b["headers"],
        )
        assert r.status_code == 400

    def test_password_change_success_allows_login_with_new_password(self, client):
        """
        CATEGORY: Authentication
        TITLE: Successful password change actually takes effect
        OBJECTIVE: End-to-end check: change password, then confirm login works
            with the NEW password and fails with the OLD one.
        EXPECTED: Change returns 200; login with new password succeeds; login
            with old password returns 401.
        SEVERITY: HIGH
        """
        payload = _valid_payload()
        reg = client.post(REGISTER, json=payload)
        headers = {"Authorization": f"Bearer {reg.json()['token']}"}

        change = client.patch(
            PASSWORD,
            json={"currentPassword": payload["password"], "newPassword": "brandNewPass123"},
            headers=headers,
        )
        assert change.status_code == 200

        new_login = client.post(LOGIN, json={"email": payload["email"], "password": "brandNewPass123"})
        assert new_login.status_code == 200

        old_login = client.post(LOGIN, json={"email": payload["email"], "password": payload["password"]})
        assert old_login.status_code == 401
