"""
Input validation tests: confirms each route's zod schema boundaries are
actually enforced by the running server, not just present in source.
Every "should reject" expectation here was checked against the real zod
schema in isolation before being written (see comments), so a failure
means a genuine behavioral mismatch, not a guess about zod's regex.
"""
import uuid

import pytest

from config import API_PREFIX
from utils.payloads import OVERSIZED_BUT_ZOD_VALID_EMAIL, long_string

HEALTH_PROFILE = f"{API_PREFIX}/health-profile"
PROGRESS = f"{API_PREFIX}/progress"
ORDERS = f"{API_PREFIX}/orders"
CHAT = f"{API_PREFIX}/chat"
REGISTER = f"{API_PREFIX}/auth/register"
MEALS = f"{API_PREFIX}/meals"


def _valid_health_profile(**overrides):
    payload = {
        "currentWeightKg": 65,
        "targetWeightKg": 60,
        "activityLevel": "MODERATE",
        "fitnessGoal": "WEIGHT_LOSS",
        "dietaryPreference": "VEGETARIAN",
        "allergies": [],
        "dailyBudget": 400,
    }
    payload.update(overrides)
    return payload


class TestRegisterEmailBoundary:
    def test_email_with_no_max_length_is_accepted(self, client):
        """
        CATEGORY: Input Validation
        TITLE: [FINDING] Email field has no maximum length constraint
        OBJECTIVE: zod's z.string().email() enforces email *shape* but not
            length. Confirmed directly against the schema in isolation that a
            300+ character local-part email string parses as VALID.
        EXPECTED: 201 -- this documents current (accepted) behavior. Consider
            adding .max(254) (RFC 5321 practical limit) to the schema; low
            impact since the column is unbounded text, but unbounded
            attacker-controlled string storage is worth a deliberate limit.
        SEVERITY: LOW
        """
        # Prefix with a run-unique token so re-running the suite against a
        # persistent database doesn't collide with a previous run's account.
        unique_email = f"{uuid.uuid4().hex[:8]}-{OVERSIZED_BUT_ZOD_VALID_EMAIL}"
        r = client.post(
            REGISTER,
            json={"name": "Boundary Test", "email": unique_email, "password": "validpass1"},
        )
        assert r.status_code == 201


class TestHealthProfileValidation:
    @pytest.mark.parametrize("field", ["currentWeightKg", "targetWeightKg", "activityLevel", "fitnessGoal", "dietaryPreference", "dailyBudget"])
    def test_health_profile_missing_required_field_rejected(self, client, user_a, field):
        """
        CATEGORY: Input Validation
        TITLE: Health profile schema enforces required fields
        OBJECTIVE: Confirm each required field in profileSchema is actually required.
        EXPECTED: 400 when the field is absent.
        SEVERITY: MEDIUM
        """
        payload = _valid_health_profile()
        del payload[field]
        r = client.post(HEALTH_PROFILE, json=payload, headers=user_a["headers"])
        assert r.status_code == 400

    @pytest.mark.parametrize("field", ["currentWeightKg", "targetWeightKg", "dailyBudget"])
    def test_health_profile_rejects_zero_or_negative_numeric_fields(self, client, user_a, field):
        """
        CATEGORY: Input Validation
        TITLE: Health profile rejects non-positive numeric values
        OBJECTIVE: currentWeightKg/targetWeightKg/dailyBudget all use z.number().positive().
        EXPECTED: 400 for 0 and for a negative value.
        SEVERITY: MEDIUM
        """
        for bad_value in (0, -10):
            payload = _valid_health_profile(**{field: bad_value})
            r = client.post(HEALTH_PROFILE, json=payload, headers=user_a["headers"])
            assert r.status_code == 400, f"{field}={bad_value} should be rejected"

    def test_health_profile_rejects_invalid_activity_level_enum(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Invalid activityLevel enum value rejected
        OBJECTIVE: Confirm the 5-value enum is enforced.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(HEALTH_PROFILE, json=_valid_health_profile(activityLevel="EXTREME"), headers=user_a["headers"])
        assert r.status_code == 400

    def test_health_profile_rejects_invalid_fitness_goal_enum(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Invalid fitnessGoal enum value rejected
        OBJECTIVE: Confirm the 4-value enum is enforced.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(HEALTH_PROFILE, json=_valid_health_profile(fitnessGoal="GET_SHREDDED"), headers=user_a["headers"])
        assert r.status_code == 400

    def test_health_profile_rejects_invalid_dietary_preference_enum(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Invalid dietaryPreference enum value rejected
        OBJECTIVE: Confirm the 3-value enum is enforced.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(HEALTH_PROFILE, json=_valid_health_profile(dietaryPreference="CARNIVORE"), headers=user_a["headers"])
        assert r.status_code == 400

    def test_health_profile_allergies_defaults_to_empty_array_when_omitted(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: allergies field defaults correctly when omitted
        OBJECTIVE: profileSchema declares allergies as z.array(z.string()).default([]).
        EXPECTED: 201 when allergies is omitted entirely (not required).
        SEVERITY: LOW
        """
        payload = _valid_health_profile()
        del payload["allergies"]
        r = client.post(HEALTH_PROFILE, json=payload, headers=user_a["headers"])
        assert r.status_code == 201

    def test_health_profile_rejects_non_array_allergies(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: allergies field rejects wrong type
        OBJECTIVE: Confirm passing a string instead of an array is rejected, not coerced.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(HEALTH_PROFILE, json=_valid_health_profile(allergies="peanuts"), headers=user_a["headers"])
        assert r.status_code == 400

    def test_health_profile_rejects_string_where_number_expected(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Numeric field rejects a string value (no implicit coercion)
        OBJECTIVE: zod's z.number() does not coerce "65" (string) to 65 (number)
            by default; confirm the API does not accidentally use z.coerce.number().
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(HEALTH_PROFILE, json=_valid_health_profile(currentWeightKg="65"), headers=user_a["headers"])
        assert r.status_code == 400

    def test_health_profile_requires_auth(self, client):
        """
        CATEGORY: Input Validation
        TITLE: Health profile submission requires authentication
        OBJECTIVE: Confirm auth is checked even with a perfectly valid body.
        EXPECTED: 401.
        SEVERITY: HIGH
        """
        r = client.post(HEALTH_PROFILE, json=_valid_health_profile())
        assert r.status_code == 401

    def test_health_profile_requires_basic_profile_completed_first(self, client):
        """
        CATEGORY: Input Validation
        TITLE: Health profile requires age/gender/height already on the account
        OBJECTIVE: healthProfile.routes.ts checks user.age/gender/heightCm before
            allowing a health assessment (needed for BMR calculation). Register
            a user WITHOUT those optional fields, then attempt the assessment.
        EXPECTED: 400 with a message about completing the basic profile first.
        SEVERITY: MEDIUM
        """
        email = f"no-basics-{uuid.uuid4().hex[:10]}@backendtests.local"
        reg = client.post(REGISTER, json={"name": "No Basics", "email": email, "password": "validpass1"})
        assert reg.status_code == 201
        headers = {"Authorization": f"Bearer {reg.json()['token']}"}
        r = client.post(HEALTH_PROFILE, json=_valid_health_profile(), headers=headers)
        assert r.status_code == 400

    def test_health_profile_huge_daily_budget_accepted_no_upper_bound(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: dailyBudget has no upper bound
        OBJECTIVE: z.number().positive() has no .max() -- confirm an
            unreasonably large budget (e.g. 10 million) is still accepted.
        EXPECTED: 201. Documents that budget-based meal filtering could be
            trivially bypassed by submitting an inflated budget; low severity
            since it only affects what's shown to the user themselves.
        SEVERITY: LOW
        """
        r = client.post(HEALTH_PROFILE, json=_valid_health_profile(dailyBudget=10_000_000), headers=user_a["headers"])
        assert r.status_code == 201


class TestProgressLogValidation:
    def test_progress_log_all_fields_optional_empty_body_accepted(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Progress log accepts an empty body
        OBJECTIVE: Every field in logSchema is .optional(). Confirm {} is valid.
        EXPECTED: 201 with a log entry containing only defaults/nulls.
        SEVERITY: LOW
        """
        r = client.post(PROGRESS, json={}, headers=user_a["headers"])
        assert r.status_code == 201

    @pytest.mark.parametrize("field", ["caloriesConsumed", "proteinConsumedG", "carbsConsumedG", "fatConsumedG"])
    def test_progress_log_rejects_negative_nutrition_values(self, client, user_a, field):
        """
        CATEGORY: Input Validation
        TITLE: Progress log rejects negative consumption values
        OBJECTIVE: These fields use z.number().nonnegative().
        EXPECTED: 400 for a negative value.
        SEVERITY: MEDIUM
        """
        r = client.post(PROGRESS, json={field: -50}, headers=user_a["headers"])
        assert r.status_code == 400

    def test_progress_log_accepts_zero_for_nonnegative_fields(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Zero is a valid boundary for nonnegative fields
        OBJECTIVE: nonnegative() means >= 0, so 0 itself must be accepted (not
            just values strictly greater than 0).
        EXPECTED: 201.
        SEVERITY: LOW
        """
        r = client.post(PROGRESS, json={"caloriesConsumed": 0}, headers=user_a["headers"])
        assert r.status_code == 201

    def test_progress_log_rejects_negative_or_zero_weight(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: weightKg uses positive(), stricter than the nonnegative nutrition fields
        OBJECTIVE: Confirm weightKg=0 is rejected (positive() excludes 0),
            unlike caloriesConsumed=0 which is valid.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(PROGRESS, json={"weightKg": 0}, headers=user_a["headers"])
        assert r.status_code == 400

    def test_progress_log_requires_auth(self, client):
        """
        CATEGORY: Input Validation
        TITLE: Progress log requires authentication
        OBJECTIVE: Confirm requireAuth guards this endpoint.
        EXPECTED: 401.
        SEVERITY: HIGH
        """
        r = client.post(PROGRESS, json={"caloriesConsumed": 500})
        assert r.status_code == 401

    def test_progress_log_notes_field_accepts_long_text(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: notes field has no length cap
        OBJECTIVE: notes uses a bare z.string().optional() with no .max().
        EXPECTED: 201 for a 5,000-character notes value.
        SEVERITY: LOW
        """
        r = client.post(PROGRESS, json={"notes": long_string(5000)}, headers=user_a["headers"])
        assert r.status_code == 201


class TestOrderValidation:
    def test_order_rejects_non_uuid_meal_id(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Order rejects a mealId that isn't a UUID
        OBJECTIVE: orderSchema uses z.string().uuid().
        EXPECTED: 400.
        SEVERITY: MEDIUM
        """
        r = client.post(ORDERS, json={"mealId": "not-a-uuid", "platform": "SWIGGY"}, headers=user_a["headers"])
        assert r.status_code == 400

    def test_order_rejects_wellformed_uuid_that_does_not_exist(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Order rejects a syntactically valid but nonexistent mealId
        OBJECTIVE: Confirm the route does its own existence check beyond
            schema-level UUID shape validation.
        EXPECTED: 404, not 400 or 500 (the meal lookup fails after validation passes).
        SEVERITY: MEDIUM
        """
        r = client.post(ORDERS, json={"mealId": str(uuid.uuid4()), "platform": "SWIGGY"}, headers=user_a["headers"])
        assert r.status_code == 404

    def test_order_rejects_invalid_platform_enum(self, client, user_a, any_meal_id):
        """
        CATEGORY: Input Validation
        TITLE: Order rejects a platform outside SWIGGY/ZOMATO
        OBJECTIVE: Confirm the enum is enforced.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(ORDERS, json={"mealId": any_meal_id, "platform": "UBEREATS"}, headers=user_a["headers"])
        assert r.status_code == 400

    def test_order_requires_auth(self, client, any_meal_id):
        """
        CATEGORY: Input Validation
        TITLE: Order placement requires authentication
        OBJECTIVE: Confirm requireAuth guards this endpoint.
        EXPECTED: 401.
        SEVERITY: HIGH
        """
        r = client.post(ORDERS, json={"mealId": any_meal_id, "platform": "SWIGGY"})
        assert r.status_code == 401


class TestChatValidation:
    def test_chat_rejects_empty_message(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Chat rejects an empty message
        OBJECTIVE: chatSchema uses z.string().min(1).
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(CHAT, json={"message": ""}, headers=user_a["headers"])
        assert r.status_code == 400

    def test_chat_rejects_message_over_500_chars(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Chat rejects a message over the 500-character cap
        OBJECTIVE: chatSchema uses z.string().max(500).
        EXPECTED: 400 for a 501-character message.
        SEVERITY: LOW
        """
        r = client.post(CHAT, json={"message": long_string(501)}, headers=user_a["headers"])
        assert r.status_code == 400

    def test_chat_accepts_message_at_exactly_500_chars(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Chat accepts the exact 500-character boundary
        OBJECTIVE: Confirm max(500) means 500 is valid, not just <500.
        EXPECTED: 200.
        SEVERITY: LOW
        """
        r = client.post(CHAT, json={"message": long_string(500)}, headers=user_a["headers"])
        assert r.status_code == 200

    def test_chat_requires_auth(self, client):
        """
        CATEGORY: Input Validation
        TITLE: Chat requires authentication
        OBJECTIVE: Confirm requireAuth guards this endpoint.
        EXPECTED: 401.
        SEVERITY: HIGH
        """
        r = client.post(CHAT, json={"message": "hello"})
        assert r.status_code == 401

    def test_chat_missing_message_field_rejected(self, client, user_a):
        """
        CATEGORY: Input Validation
        TITLE: Chat rejects a body with no message field at all
        OBJECTIVE: Confirm the field is required, not just constrained when present.
        EXPECTED: 400.
        SEVERITY: LOW
        """
        r = client.post(CHAT, json={}, headers=user_a["headers"])
        assert r.status_code == 400


class TestMealQueryValidation:
    def test_meals_unknown_query_param_is_silently_ignored(self, client):
        """
        CATEGORY: Input Validation
        TITLE: Unrecognized query params on GET /meals don't error
        OBJECTIVE: The route only destructures mealType/cuisine/platform from
            req.query; anything else should simply be ignored, not cause a 500.
        EXPECTED: 200.
        SEVERITY: LOW
        """
        r = client.get(MEALS, params={"sort": "price_desc", "foo": "bar"})
        assert r.status_code == 200

    def test_meals_invalid_meal_type_crashes_the_server_process(self, client):
        """
        CATEGORY: Input Validation
        TITLE: [FINDING] Invalid mealType/platform query value crashes the entire backend process (unauthenticated DoS)
        OBJECTIVE: meal.routes.ts casts req.query.mealType and req.query.platform
            directly to their Prisma enum types with no runtime validation
            (`mealType as MealType`) before passing them into a `where` filter.
            mealType and platform are native Postgres enum columns
            (`enum MealType {...}` / `enum Platform {...}` in schema.prisma).
            An out-of-enum string causes Postgres/Prisma to reject the query
            with a real error; the async route handler has no try/catch, and
            Express 4 does not auto-catch rejected promises from async
            handlers, so the rejection is unhandled at the process level --
            which crashes the whole Node process under Node's default
            `--unhandled-rejections=throw` behavior.
            CONFIRMED IN CI against real Postgres (not the in-memory stand-in
            used to build this suite): after this exact request, every
            subsequent request in the same run got
            `httpcore.ConnectError: Connection refused` -- the server never
            came back until manually restarted. The in-memory stub used
            during initial development didn't reproduce this because it has
            no enum-type validation layer at all, which is exactly why this
            class of bug needs a real database to catch -- see
            reports/backend-inventory.md for the full incident writeup.
        EXPECTED (documents the confirmed, real, unauthenticated vulnerability):
            **This should return 200 with an empty (or 400 with a validation
            error) result and never take the server down.** As currently
            deployed, it takes the whole process down with a single
            unauthenticated GET request -- repeatable in a loop for a
            trivial, complete denial of service against every endpoint,
            not just this one. Remediation: validate mealType/platform
            against the enum's allowed values (e.g. via a small zod enum
            check) before building the Prisma `where` clause, and wrap this
            handler's body in try/catch (or adopt a global async-handler
            wrapper) so a bad query string degrades to a 400, never a crash.
            The identical pattern exists in recommendation.routes.ts's
            mealType query param too -- see test_business_logic.py /
            security-review.md for that companion finding.
        SEVERITY: CRITICAL
        """
        r = client.get(MEALS, params={"mealType": "MIDNIGHT_SNACK"})
        assert r.status_code in (200, 400), (
            f"got {r.status_code} (or the request failed at the transport level entirely) -- "
            f"if this test errored rather than failed, the server likely crashed. "
            f"See the CRITICAL finding in security-review.md (DOS-1)."
        )
        if r.status_code == 200:
            assert r.json()["meals"] == []

        # If the process survived, confirm it's still actually serving requests
        # (a partial crash/restart-loop would still be a serious problem even
        # if this one response looks fine).
        health = client.get("/health")
        assert health.status_code == 200

    def test_meals_invalid_platform_does_not_crash_the_server(self, client):
        """
        CATEGORY: Input Validation
        TITLE: [FINDING] Invalid platform query value has the same unvalidated-enum crash risk as mealType
        OBJECTIVE: Same root cause as the mealType finding above --
            `platform: platform as Platform` on the same GET /api/meals
            route, also cast with zero runtime validation. Tested
            separately since it's a distinct query parameter an attacker
            (or a confused client) could hit independently.
        EXPECTED: 200 with an empty list, or 400 -- never a crash.
        SEVERITY: CRITICAL
        """
        r = client.get(MEALS, params={"platform": "UBEREATS_NOT_A_REAL_PLATFORM"})
        assert r.status_code in (200, 400)
        if r.status_code == 200:
            assert r.json()["meals"] == []
        assert client.get("/health").status_code == 200

    def test_meal_by_id_nonexistent_uuid_returns_404(self, client):
        """
        CATEGORY: Input Validation
        TITLE: GET /meals/:id with a well-formed but nonexistent id returns 404
        OBJECTIVE: Confirm the not-found path, distinct from a malformed-id path.
        EXPECTED: 404.
        SEVERITY: LOW
        """
        r = client.get(f"{MEALS}/{uuid.uuid4()}")
        assert r.status_code == 404

    def test_meal_by_id_non_uuid_id_does_not_500(self, client):
        """
        CATEGORY: Input Validation
        TITLE: GET /meals/:id with a non-UUID id string doesn't crash
        OBJECTIVE: Unlike /api/orders, this route does not validate that :id
            is a UUID before querying, and Meal.id is a plain `String @id`
            column (not a native Postgres UUID type per schema.prisma), so a
            non-UUID string is a legal (if never-matching) equality filter.
        EXPECTED: 404 -- the lookup runs, finds nothing, and the route's
            existing `if (!meal) return 404` path handles it. Never a 500.
        SEVERITY: LOW
        """
        r = client.get(f"{MEALS}/not-a-uuid-at-all")
        assert r.status_code == 404
