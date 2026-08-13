"""
Functional API tests: broad happy-path + expected-error-path coverage
across every endpoint, independent of the deeper security/business-logic
scenarios covered elsewhere. This file answers "does the basic contract of
every endpoint work" -- status codes, response shape, and simple round trips.
"""
import uuid

import pytest

from config import API_PREFIX

REGISTER = f"{API_PREFIX}/auth/register"
LOGIN = f"{API_PREFIX}/auth/login"
ME = f"{API_PREFIX}/auth/me"
PROFILE = f"{API_PREFIX}/auth/profile"
PASSWORD = f"{API_PREFIX}/auth/password"
HEALTH_PROFILE = f"{API_PREFIX}/health-profile"
MEALS = f"{API_PREFIX}/meals"
RECOMMENDATIONS = f"{API_PREFIX}/recommendations"
MEAL_PLAN_GENERATE = f"{API_PREFIX}/meal-plans/generate"
MEAL_PLAN_CURRENT = f"{API_PREFIX}/meal-plans/current"
ORDERS = f"{API_PREFIX}/orders"
PROGRESS = f"{API_PREFIX}/progress"
PROGRESS_SUMMARY = f"{API_PREFIX}/progress/summary"
PROGRESS_WEIGHT_HISTORY = f"{API_PREFIX}/progress/weight-history"
CHAT = f"{API_PREFIX}/chat"


def _fresh_user(client, with_profile=False):
    email = f"func-{uuid.uuid4().hex[:12]}@backendtests.local"
    r = client.post(
        REGISTER,
        json={"name": "Functional Tester", "email": email, "password": "validpass1", "age": 30, "gender": "MALE", "heightCm": 175, "weightKg": 75},
    )
    assert r.status_code == 201
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    if with_profile:
        p = client.post(
            HEALTH_PROFILE,
            json={
                "currentWeightKg": 75, "targetWeightKg": 72, "activityLevel": "MODERATE",
                "fitnessGoal": "MAINTENANCE", "dietaryPreference": "NON_VEGETARIAN", "allergies": [], "dailyBudget": 500,
            },
            headers=headers,
        )
        assert p.status_code == 201
    return {"email": email, "headers": headers, "id": r.json()["user"]["id"]}


# ─── Health ─────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_check_returns_200(self, client):
        """
        CATEGORY: Functional
        TITLE: GET /health returns 200
        OBJECTIVE: Basic liveness check.
        EXPECTED: 200.
        SEVERITY: LOW
        """
        assert client.get("/health").status_code == 200

    def test_health_check_reports_correct_service_name(self, client):
        """
        CATEGORY: Functional
        TITLE: /health reports service:"fitfuel-backend"
        OBJECTIVE: Confirm the identifying field is correct (useful for
            multi-service monitoring dashboards).
        EXPECTED: body.service == "fitfuel-backend".
        SEVERITY: LOW
        """
        assert client.get("/health").json()["service"] == "fitfuel-backend"


# ─── Auth: functional round trips (deeper edge cases live in test_authentication.py) ──

class TestAuthFunctional:
    def test_full_register_login_me_round_trip(self, client):
        """
        CATEGORY: Functional
        TITLE: Register -> login -> /me round trip returns consistent identity
        OBJECTIVE: End-to-end happy path through the three core auth calls.
        EXPECTED: All three calls succeed and report the same user id/email.
        SEVERITY: HIGH
        """
        email = f"roundtrip-{uuid.uuid4().hex[:10]}@backendtests.local"
        reg = client.post(REGISTER, json={"name": "Round Trip", "email": email, "password": "validpass1"})
        assert reg.status_code == 201
        uid = reg.json()["user"]["id"]

        login = client.post(LOGIN, json={"email": email, "password": "validpass1"})
        assert login.status_code == 200
        assert login.json()["user"]["id"] == uid

        me = client.get(ME, headers={"Authorization": f"Bearer {login.json()['token']}"})
        assert me.status_code == 200
        assert me.json()["user"]["id"] == uid
        assert me.json()["user"]["email"] == email

    def test_me_returns_optional_profile_fields_when_present(self, client):
        """
        CATEGORY: Functional
        TITLE: /me includes age/gender/heightCm/weightKg when supplied at registration
        OBJECTIVE: Confirm the select clause in /me returns the optional
            profile fields, not just id/name/email.
        EXPECTED: 200, response includes age, gender, heightCm, weightKg matching registration.
        SEVERITY: MEDIUM
        """
        user = _fresh_user(client)
        r = client.get(ME, headers=user["headers"])
        body = r.json()["user"]
        assert body["age"] == 30
        assert body["gender"] == "MALE"
        assert body["heightCm"] == 175
        assert body["weightKg"] == 75

    @pytest.mark.parametrize("http_method", ["get", "post", "put", "delete"])
    def test_profile_endpoint_only_accepts_patch(self, client, user_a, http_method):
        """
        CATEGORY: Functional
        TITLE: /api/auth/profile only responds to PATCH
        OBJECTIVE: Confirm other verbs on the same path are not accidentally routed.
        EXPECTED: 404 for GET/POST/PUT/DELETE on this path.
        SEVERITY: LOW
        """
        r = getattr(client, http_method)(PROFILE, headers=user_a["headers"])
        assert r.status_code == 404


# ─── Health profile ─────────────────────────────────────────────────────

class TestHealthProfileFunctional:
    def test_submit_and_retrieve_health_profile(self, client):
        """
        CATEGORY: Functional
        TITLE: Submitted health profile can be retrieved afterwards
        OBJECTIVE: POST then GET round trip.
        EXPECTED: GET returns 200 with matching currentWeightKg.
        SEVERITY: HIGH
        """
        user = _fresh_user(client, with_profile=True)
        r = client.get(HEALTH_PROFILE, headers=user["headers"])
        assert r.status_code == 200
        assert r.json()["profile"]["currentWeightKg"] == 75

    def test_resubmitting_health_profile_updates_in_place(self, client):
        """
        CATEGORY: Functional
        TITLE: Resubmitting a health profile updates rather than duplicates (upsert)
        OBJECTIVE: profileSchema.upsert() should update the existing row.
        EXPECTED: Second submission's weight is reflected on GET; no error about duplicates.
        SEVERITY: MEDIUM
        """
        user = _fresh_user(client, with_profile=True)
        second = client.post(
            HEALTH_PROFILE,
            json={"currentWeightKg": 70, "targetWeightKg": 68, "activityLevel": "LIGHT", "fitnessGoal": "MAINTENANCE", "dietaryPreference": "VEGETARIAN", "allergies": [], "dailyBudget": 400},
            headers=user["headers"],
        )
        assert second.status_code == 201
        got = client.get(HEALTH_PROFILE, headers=user["headers"])
        assert got.json()["profile"]["currentWeightKg"] == 70

    def test_health_profile_not_found_before_submission(self, client):
        """
        CATEGORY: Functional
        TITLE: GET health profile before ever submitting one returns 404
        OBJECTIVE: Confirm the not-found path for a brand new user.
        EXPECTED: 404.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.get(HEALTH_PROFILE, headers=user["headers"])
        assert r.status_code == 404

    def test_health_profile_response_includes_explanation_field(self, client):
        """
        CATEGORY: Functional
        TITLE: Health profile submission response includes an explanation field
        OBJECTIVE: The route always includes an "explanation" key (string or
            null -- null when the optional LLM call fails/is unconfigured).
        EXPECTED: "explanation" key present in the response body.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.post(
            HEALTH_PROFILE,
            json={"currentWeightKg": 75, "targetWeightKg": 72, "activityLevel": "MODERATE", "fitnessGoal": "MAINTENANCE", "dietaryPreference": "NON_VEGETARIAN", "allergies": [], "dailyBudget": 500},
            headers=user["headers"],
        )
        assert "explanation" in r.json()


# ─── Meals catalog ──────────────────────────────────────────────────────

class TestMealsFunctional:
    def test_list_meals_returns_200_and_array(self, client):
        """
        CATEGORY: Functional
        TITLE: GET /meals returns a meals array
        OBJECTIVE: Basic catalog listing.
        EXPECTED: 200, "meals" is a list.
        SEVERITY: HIGH
        """
        r = client.get(MEALS)
        assert r.status_code == 200
        assert isinstance(r.json()["meals"], list)

    def test_list_meals_no_auth_required(self, client):
        """
        CATEGORY: Functional
        TITLE: Meal catalog is public
        OBJECTIVE: Confirm GET /meals has no requireAuth (unlike almost every
            other resource in the API).
        EXPECTED: 200 with no Authorization header.
        SEVERITY: LOW
        """
        r = client.get(MEALS)
        assert r.status_code == 200

    @pytest.mark.parametrize("meal_type", ["BREAKFAST", "LUNCH", "DINNER", "SNACK"])
    def test_filter_meals_by_type_returns_only_that_type(self, client, meal_type):
        """
        CATEGORY: Functional
        TITLE: mealType filter returns only meals of that type
        OBJECTIVE: Confirm the where-clause filter is applied correctly for
            every one of the 4 meal types.
        EXPECTED: Every returned meal's mealType matches the filter.
        SEVERITY: MEDIUM
        """
        r = client.get(MEALS, params={"mealType": meal_type})
        assert r.status_code == 200
        for meal in r.json()["meals"]:
            assert meal["mealType"] == meal_type

    def test_meals_are_capped_at_100_results(self, client):
        """
        CATEGORY: Functional
        TITLE: Meal catalog listing is capped at 100 (take: 100)
        OBJECTIVE: Confirm the route's hardcoded take:100 limit holds even
            with no filters applied.
        EXPECTED: len(meals) <= 100.
        SEVERITY: LOW
        """
        r = client.get(MEALS)
        assert len(r.json()["meals"]) <= 100

    def test_meals_sorted_by_health_score_descending(self, client):
        """
        CATEGORY: Functional
        TITLE: Meal catalog is sorted by healthScore descending by default
        OBJECTIVE: orderBy: {healthScore: "desc"}.
        EXPECTED: healthScore sequence is non-increasing.
        SEVERITY: LOW
        """
        r = client.get(MEALS)
        scores = [m["healthScore"] for m in r.json()["meals"]]
        assert scores == sorted(scores, reverse=True)

    def test_get_single_meal_by_id(self, client, any_meal_id):
        """
        CATEGORY: Functional
        TITLE: GET /meals/:id returns the specific meal
        OBJECTIVE: Basic single-resource lookup.
        EXPECTED: 200, returned meal.id matches the requested id.
        SEVERITY: MEDIUM
        """
        r = client.get(f"{MEALS}/{any_meal_id}")
        assert r.status_code == 200
        assert r.json()["meal"]["id"] == any_meal_id

    def test_single_meal_includes_full_nutrition_fields(self, client, any_meal_id):
        """
        CATEGORY: Functional
        TITLE: Single meal response includes nutrition fields
        OBJECTIVE: Confirm calories/proteinG/carbsG/fatG/price are all present
            (needed by the mobile/web client to render a meal card).
        EXPECTED: All five fields present and numeric.
        SEVERITY: LOW
        """
        r = client.get(f"{MEALS}/{any_meal_id}")
        meal = r.json()["meal"]
        for field in ("calories", "proteinG", "carbsG", "fatG", "price"):
            assert isinstance(meal[field], (int, float)), f"{field} missing or non-numeric"


# ─── Recommendations ────────────────────────────────────────────────────

class TestRecommendationsFunctional:
    @pytest.mark.parametrize("meal_type", ["BREAKFAST", "LUNCH", "DINNER", "SNACK"])
    def test_recommendations_for_each_meal_type(self, client, meal_type):
        """
        CATEGORY: Functional
        TITLE: Recommendations work for every meal type
        OBJECTIVE: Confirm the endpoint doesn't only work for the default (LUNCH).
        EXPECTED: 200, "recommendations" is a list.
        SEVERITY: MEDIUM
        """
        user = _fresh_user(client, with_profile=True)
        r = client.get(RECOMMENDATIONS, params={"mealType": meal_type}, headers=user["headers"])
        assert r.status_code == 200
        assert isinstance(r.json()["recommendations"], list)

    def test_recommendation_items_include_score_breakdown(self, client):
        """
        CATEGORY: Functional
        TITLE: Each recommendation includes a score breakdown
        OBJECTIVE: Confirm the response shape includes breakdown.{calorieAccuracy,
            proteinQuality,budgetFit,healthScore}, used by the client UI.
        EXPECTED: breakdown object present with all 4 sub-scores.
        SEVERITY: LOW
        """
        user = _fresh_user(client, with_profile=True)
        r = client.get(RECOMMENDATIONS, headers=user["headers"])
        recs = r.json()["recommendations"]
        if recs:
            breakdown = recs[0]["breakdown"]
            for key in ("calorieAccuracy", "proteinQuality", "budgetFit", "healthScore"):
                assert key in breakdown


# ─── Meal plans ─────────────────────────────────────────────────────────

class TestMealPlanFunctional:
    def test_generate_then_fetch_current_meal_plan(self, client):
        """
        CATEGORY: Functional
        TITLE: Generated meal plan is retrievable via /current afterwards
        OBJECTIVE: POST /generate then GET /current round trip.
        EXPECTED: GET /current returns the same plan id just generated.
        SEVERITY: HIGH
        """
        user = _fresh_user(client, with_profile=True)
        gen = client.post(MEAL_PLAN_GENERATE, headers=user["headers"])
        assert gen.status_code == 201
        plan_id = gen.json()["mealPlan"]["id"]

        current = client.get(MEAL_PLAN_CURRENT, headers=user["headers"])
        assert current.status_code == 200
        assert current.json()["mealPlan"]["id"] == plan_id

    def test_regenerating_meal_plan_creates_a_new_plan(self, client):
        """
        CATEGORY: Functional
        TITLE: Calling generate twice creates two distinct plans, /current returns the newest
        OBJECTIVE: Confirm generate always creates a new row rather than
            updating in place, and /current's orderBy:{createdAt:"desc"} picks the latest.
        EXPECTED: Two different plan ids; /current matches the second one.
        SEVERITY: MEDIUM
        """
        user = _fresh_user(client, with_profile=True)
        first = client.post(MEAL_PLAN_GENERATE, headers=user["headers"])
        second = client.post(MEAL_PLAN_GENERATE, headers=user["headers"])
        assert first.json()["mealPlan"]["id"] != second.json()["mealPlan"]["id"]

        current = client.get(MEAL_PLAN_CURRENT, headers=user["headers"])
        assert current.json()["mealPlan"]["id"] == second.json()["mealPlan"]["id"]

    def test_current_meal_plan_before_any_generation_returns_404(self, client):
        """
        CATEGORY: Functional
        TITLE: /current before any plan exists returns 404
        OBJECTIVE: Confirm the not-found path for a user who has a health
            profile but hasn't generated a plan yet.
        EXPECTED: 404.
        SEVERITY: LOW
        """
        user = _fresh_user(client, with_profile=True)
        r = client.get(MEAL_PLAN_CURRENT, headers=user["headers"])
        assert r.status_code == 404

    def test_meal_plan_items_include_full_meal_details(self, client):
        """
        CATEGORY: Functional
        TITLE: Meal plan items are hydrated with full meal details, not just ids
        OBJECTIVE: Confirm include:{items:{include:{meal:true}}} actually
            populates the nested meal object.
        EXPECTED: Every item has a non-null "meal" object with a "name" field.
        SEVERITY: MEDIUM
        """
        user = _fresh_user(client, with_profile=True)
        gen = client.post(MEAL_PLAN_GENERATE, headers=user["headers"])
        for item in gen.json()["mealPlan"]["items"]:
            assert item["meal"] is not None
            assert "name" in item["meal"]


# ─── Orders ─────────────────────────────────────────────────────────────

class TestOrdersFunctional:
    def test_place_order_then_see_it_in_list(self, client, any_meal_id):
        """
        CATEGORY: Functional
        TITLE: Placed order appears in the order list afterwards
        OBJECTIVE: POST then GET round trip.
        EXPECTED: The new order's id is present in GET /orders.
        SEVERITY: HIGH
        """
        user = _fresh_user(client)
        placed = client.post(ORDERS, json={"mealId": any_meal_id, "platform": "SWIGGY"}, headers=user["headers"])
        assert placed.status_code == 201
        order_id = placed.json()["order"]["id"]

        listed = client.get(ORDERS, headers=user["headers"])
        ids = [o["id"] for o in listed.json()["orders"]]
        assert order_id in ids

    def test_order_list_empty_for_brand_new_user(self, client):
        """
        CATEGORY: Functional
        TITLE: Order list is empty before any orders are placed
        OBJECTIVE: Confirm the baseline (empty) state.
        EXPECTED: 200, empty list.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.get(ORDERS, headers=user["headers"])
        assert r.status_code == 200
        assert r.json()["orders"] == []

    def test_order_includes_hydrated_meal_details(self, client, any_meal_id):
        """
        CATEGORY: Functional
        TITLE: Order list items include the full meal object
        OBJECTIVE: Confirm include:{meal:true} on the orders query.
        EXPECTED: order.meal.name present.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        client.post(ORDERS, json={"mealId": any_meal_id, "platform": "ZOMATO"}, headers=user["headers"])
        listed = client.get(ORDERS, headers=user["headers"])
        assert "name" in listed.json()["orders"][0]["meal"]

    def test_multiple_orders_listed_most_recent_first(self, client, any_meal_id):
        """
        CATEGORY: Functional
        TITLE: Orders list is sorted newest first
        OBJECTIVE: orderBy: {createdAt: "desc"}.
        EXPECTED: Second-placed order appears before the first in the list.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        first = client.post(ORDERS, json={"mealId": any_meal_id, "platform": "SWIGGY"}, headers=user["headers"])
        second = client.post(ORDERS, json={"mealId": any_meal_id, "platform": "ZOMATO"}, headers=user["headers"])
        listed = client.get(ORDERS, headers=user["headers"]).json()["orders"]
        ids_in_order = [o["id"] for o in listed]
        assert ids_in_order.index(second.json()["order"]["id"]) < ids_in_order.index(first.json()["order"]["id"])


# ─── Progress ───────────────────────────────────────────────────────────

class TestProgressFunctional:
    def test_log_progress_then_see_it_in_list(self, client):
        """
        CATEGORY: Functional
        TITLE: Logged progress entry appears in the progress list afterwards
        OBJECTIVE: POST then GET round trip.
        EXPECTED: 201 on create; list length increases by 1.
        SEVERITY: HIGH
        """
        user = _fresh_user(client)
        before = client.get(PROGRESS, headers=user["headers"]).json()["logs"]
        create = client.post(PROGRESS, json={"weightKg": 74, "caloriesConsumed": 2000}, headers=user["headers"])
        assert create.status_code == 201
        after = client.get(PROGRESS, headers=user["headers"]).json()["logs"]
        assert len(after) == len(before) + 1

    def test_progress_list_capped_at_100(self, client):
        """
        CATEGORY: Functional
        TITLE: Progress list route caps results at 100 (take: 100)
        OBJECTIVE: Documents the hardcoded limit; not exercised at full scale
            here (100 real requests) but confirms the response never exceeds it
            for a normal-sized history.
        EXPECTED: len(logs) <= 100.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        for _ in range(5):
            client.post(PROGRESS, json={"caloriesConsumed": 1800}, headers=user["headers"])
        r = client.get(PROGRESS, headers=user["headers"])
        assert len(r.json()["logs"]) <= 100

    def test_weight_history_only_includes_entries_with_weight_recorded(self, client):
        """
        CATEGORY: Functional
        TITLE: Weight history excludes entries where weightKg was not logged
        OBJECTIVE: The route filters weightKg: {not: null}. Log one entry
            WITH weight and one WITHOUT, confirm only the former appears.
        EXPECTED: weight-history length reflects only the weight-bearing entry.
        SEVERITY: MEDIUM
        """
        user = _fresh_user(client)
        before = client.get(PROGRESS_WEIGHT_HISTORY, headers=user["headers"]).json()["weightHistory"]
        client.post(PROGRESS, json={"caloriesConsumed": 1800}, headers=user["headers"])  # no weight
        client.post(PROGRESS, json={"weightKg": 73.5}, headers=user["headers"])  # with weight
        after = client.get(PROGRESS_WEIGHT_HISTORY, headers=user["headers"]).json()["weightHistory"]
        assert len(after) == len(before) + 1

    def test_progress_summary_returns_expected_shape(self, client):
        """
        CATEGORY: Functional
        TITLE: /progress/summary response has the documented shape
        OBJECTIVE: Confirm logs/weeklyAverageCalories/goalAchievementPct keys are all present.
        EXPECTED: All 3 keys present.
        SEVERITY: LOW
        """
        user = _fresh_user(client, with_profile=True)
        r = client.get(PROGRESS_SUMMARY, headers=user["headers"])
        body = r.json()
        for key in ("logs", "weeklyAverageCalories", "goalAchievementPct"):
            assert key in body


# ─── Chat ───────────────────────────────────────────────────────────────

class TestChatFunctional:
    def test_chat_returns_a_reply_string(self, client):
        """
        CATEGORY: Functional
        TITLE: Chat returns a non-empty reply
        OBJECTIVE: Basic happy path -- confirm a reply is always returned,
            even without a configured Groq API key (graceful fallback).
        EXPECTED: 200, "reply" is a non-empty string.
        SEVERITY: HIGH
        """
        user = _fresh_user(client)
        r = client.post(CHAT, json={"message": "What should I eat for breakfast?"}, headers=user["headers"])
        assert r.status_code == 200
        assert isinstance(r.json()["reply"], str)
        assert len(r.json()["reply"]) > 0

    def test_chat_works_without_a_completed_health_profile(self, client):
        """
        CATEGORY: Functional
        TITLE: Chat works even before the user has a health profile
        OBJECTIVE: Unlike recommendations/meal-plan generation, chat.routes.ts
            builds a fallback contextSummary when profile is null rather than
            rejecting the request.
        EXPECTED: 200 (not 400), for a user with no health profile at all.
        SEVERITY: MEDIUM
        """
        user = _fresh_user(client)  # no profile
        r = client.post(CHAT, json={"message": "Hello"}, headers=user["headers"])
        assert r.status_code == 200


# ─── Meal object field-presence contract ───────────────────────────────

MEAL_FIELDS = [
    "id", "name", "restaurant", "platform", "cuisine", "mealType", "calories",
    "proteinG", "carbsG", "fatG", "price", "healthScore", "isVegetarian",
    "isVegan", "allergens", "imageUrl", "deepLinkQuery",
]


class TestMealObjectShape:
    @pytest.mark.parametrize("field", MEAL_FIELDS)
    def test_meal_object_includes_field(self, client, any_meal_id, field):
        """
        CATEGORY: Functional
        TITLE: Meal object includes the "{field}" field
        OBJECTIVE: Confirm the full Meal model shape is returned to clients
            (mobile/web rely on every one of these to render a meal card).
        EXPECTED: The field key is present on GET /meals/:id.
        SEVERITY: LOW
        """
        r = client.get(f"{MEALS}/{any_meal_id}")
        assert field in r.json()["meal"]


# ─── Enum coverage: every declared enum value actually works end-to-end ──

class TestEnumCoverage:
    @pytest.mark.parametrize("gender", ["MALE", "FEMALE", "OTHER"])
    def test_registration_accepts_every_gender_value(self, client, gender):
        """
        CATEGORY: Functional
        TITLE: Registration accepts gender="{gender}"
        OBJECTIVE: Confirm each of the 3 declared enum values round-trips
            correctly, not just the ones used in the shared fixtures.
        EXPECTED: 201, /me reports the same gender back.
        SEVERITY: LOW
        """
        email = f"gender-{uuid.uuid4().hex[:10]}@backendtests.local"
        r = client.post(REGISTER, json={"name": "Gender Test", "email": email, "password": "validpass1", "gender": gender})
        assert r.status_code == 201
        me = client.get(ME, headers={"Authorization": f"Bearer {r.json()['token']}"})
        assert me.json()["user"]["gender"] == gender

    @pytest.mark.parametrize("activity_level", ["SEDENTARY", "LIGHT", "MODERATE", "ACTIVE", "VERY_ACTIVE"])
    def test_health_profile_accepts_every_activity_level(self, client, activity_level):
        """
        CATEGORY: Functional
        TITLE: Health profile accepts activityLevel="{activity_level}"
        OBJECTIVE: Confirm each of the 5 declared enum values is accepted.
        EXPECTED: 201.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.post(
            HEALTH_PROFILE,
            json={"currentWeightKg": 75, "targetWeightKg": 72, "activityLevel": activity_level, "fitnessGoal": "MAINTENANCE", "dietaryPreference": "NON_VEGETARIAN", "allergies": [], "dailyBudget": 500},
            headers=user["headers"],
        )
        assert r.status_code == 201

    @pytest.mark.parametrize("fitness_goal", ["WEIGHT_LOSS", "WEIGHT_GAIN", "MUSCLE_GAIN", "MAINTENANCE"])
    def test_health_profile_accepts_every_fitness_goal(self, client, fitness_goal):
        """
        CATEGORY: Functional
        TITLE: Health profile accepts fitnessGoal="{fitness_goal}"
        OBJECTIVE: Confirm each of the 4 declared enum values is accepted.
        EXPECTED: 201.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.post(
            HEALTH_PROFILE,
            json={"currentWeightKg": 75, "targetWeightKg": 72, "activityLevel": "MODERATE", "fitnessGoal": fitness_goal, "dietaryPreference": "NON_VEGETARIAN", "allergies": [], "dailyBudget": 500},
            headers=user["headers"],
        )
        assert r.status_code == 201

    @pytest.mark.parametrize("dietary_preference", ["VEGETARIAN", "NON_VEGETARIAN", "VEGAN"])
    def test_health_profile_accepts_every_dietary_preference(self, client, dietary_preference):
        """
        CATEGORY: Functional
        TITLE: Health profile accepts dietaryPreference="{dietary_preference}"
        OBJECTIVE: Confirm each of the 3 declared enum values is accepted.
        EXPECTED: 201.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.post(
            HEALTH_PROFILE,
            json={"currentWeightKg": 75, "targetWeightKg": 72, "activityLevel": "MODERATE", "fitnessGoal": "MAINTENANCE", "dietaryPreference": dietary_preference, "allergies": [], "dailyBudget": 500},
            headers=user["headers"],
        )
        assert r.status_code == 201

    @pytest.mark.parametrize("platform", ["SWIGGY", "ZOMATO"])
    def test_orders_accept_every_platform(self, client, any_meal_id, platform):
        """
        CATEGORY: Functional
        TITLE: Orders accept platform="{platform}"
        OBJECTIVE: Confirm both declared enum values work end-to-end.
        EXPECTED: 201, order.platform echoes back the requested value.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.post(ORDERS, json={"mealId": any_meal_id, "platform": platform}, headers=user["headers"])
        assert r.status_code == 201
        assert r.json()["order"]["platform"] == platform


# ─── Progress log field round-trips ─────────────────────────────────────

PROGRESS_NUMERIC_FIELDS = [
    ("weightKg", 71.5),
    ("caloriesConsumed", 2100),
    ("proteinConsumedG", 110),
    ("carbsConsumedG", 220),
    ("fatConsumedG", 60),
]


class TestProgressFieldRoundTrip:
    @pytest.mark.parametrize("field,value", PROGRESS_NUMERIC_FIELDS, ids=[f for f, _ in PROGRESS_NUMERIC_FIELDS])
    def test_progress_field_round_trips_through_create(self, client, field, value):
        """
        CATEGORY: Functional
        TITLE: Progress log field "{field}" round-trips correctly
        OBJECTIVE: Confirm each individually-loggable metric is stored and
            echoed back accurately by the create response.
        EXPECTED: response.log[field] == value.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.post(PROGRESS, json={field: value}, headers=user["headers"])
        assert r.status_code == 201
        assert r.json()["log"][field] == value


# ─── Error response shape contract ──────────────────────────────────────

class TestErrorResponseShapeContract:
    def test_register_400_response_has_error_key(self, client):
        """
        CATEGORY: Functional
        TITLE: Register validation failure has an "error" key
        OBJECTIVE: Confirm the error response contract is consistent.
        EXPECTED: "error" present in body.
        SEVERITY: LOW
        """
        r = client.post(REGISTER, json={"email": "bad"})
        assert "error" in r.json()

    def test_login_401_response_has_error_key(self, client):
        """
        CATEGORY: Functional
        TITLE: Login failure has an "error" key
        OBJECTIVE: Confirm the error response contract is consistent.
        EXPECTED: "error" present in body.
        SEVERITY: LOW
        """
        r = client.post(LOGIN, json={"email": "nobody-here@backendtests.local", "password": "whatever1"})
        assert "error" in r.json()

    def test_order_404_response_has_error_key(self, client):
        """
        CATEGORY: Functional
        TITLE: Order-for-nonexistent-meal failure has an "error" key
        OBJECTIVE: Confirm the error response contract is consistent.
        EXPECTED: "error" present in body.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.post(ORDERS, json={"mealId": str(uuid.uuid4()), "platform": "SWIGGY"}, headers=user["headers"])
        assert "error" in r.json()

    def test_meal_not_found_404_response_has_error_key(self, client):
        """
        CATEGORY: Functional
        TITLE: Meal-not-found failure has an "error" key
        OBJECTIVE: Confirm the error response contract is consistent.
        EXPECTED: "error" present in body.
        SEVERITY: LOW
        """
        r = client.get(f"{MEALS}/{uuid.uuid4()}")
        assert "error" in r.json()

    def test_health_profile_not_found_404_response_has_error_key(self, client):
        """
        CATEGORY: Functional
        TITLE: Health-profile-not-found failure has an "error" key
        OBJECTIVE: Confirm the error response contract is consistent.
        EXPECTED: "error" present in body.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.get(HEALTH_PROFILE, headers=user["headers"])
        assert "error" in r.json()

    def test_meal_plan_generate_400_response_has_error_key(self, client):
        """
        CATEGORY: Functional
        TITLE: Meal-plan-generate-without-profile failure has an "error" key
        OBJECTIVE: Confirm the error response contract is consistent.
        EXPECTED: "error" present in body.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.post(MEAL_PLAN_GENERATE, headers=user["headers"])
        assert "error" in r.json()

    def test_recommendations_400_response_has_error_key(self, client):
        """
        CATEGORY: Functional
        TITLE: Recommendations-without-profile failure has an "error" key
        OBJECTIVE: Confirm the error response contract is consistent.
        EXPECTED: "error" present in body.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.get(RECOMMENDATIONS, headers=user["headers"])
        assert "error" in r.json()

    def test_chat_400_response_has_error_key(self, client):
        """
        CATEGORY: Functional
        TITLE: Chat validation failure has an "error" key
        OBJECTIVE: Confirm the error response contract is consistent.
        EXPECTED: "error" present in body.
        SEVERITY: LOW
        """
        user = _fresh_user(client)
        r = client.post(CHAT, json={"message": ""}, headers=user["headers"])
        assert "error" in r.json()

    def test_password_change_401_response_has_error_key(self, client, user_a):
        """
        CATEGORY: Functional
        TITLE: Wrong-current-password failure has an "error" key
        OBJECTIVE: Confirm the error response contract is consistent.
        EXPECTED: "error" present in body.
        SEVERITY: LOW
        """
        r = client.patch(PASSWORD, json={"currentPassword": "wrong", "newPassword": "newpassword1"}, headers=user_a["headers"])
        assert "error" in r.json()

    def test_unauthenticated_401_response_has_error_key(self, client):
        """
        CATEGORY: Functional
        TITLE: Missing-auth failure has an "error" key
        OBJECTIVE: Confirm the error response contract is consistent.
        EXPECTED: "error" present in body.
        SEVERITY: LOW
        """
        r = client.get(ME)
        assert "error" in r.json()


# ─── Endpoint smoke matrix: every endpoint in the inventory responds without a 5xx ──

class TestEndpointSmokeMatrix:
    def test_every_get_endpoint_responds_without_5xx_when_authenticated(self, client):
        """
        CATEGORY: Functional
        TITLE: Every GET endpoint returns a non-5xx status for an authenticated, profile-complete user
        OBJECTIVE: Broad smoke check across the full endpoint inventory in
            one pass, using a single well-prepared user, as a final safety
            net beyond the per-endpoint tests elsewhere in this file.
        EXPECTED: No GET endpoint in config.ENDPOINTS returns >= 500.
        SEVERITY: MEDIUM
        """
        from config import ENDPOINTS

        user = _fresh_user(client, with_profile=True)
        client.post(MEAL_PLAN_GENERATE, headers=user["headers"])  # so /meal-plans/current has data
        failures = []
        for method, path, requires_auth, _desc in ENDPOINTS:
            if method != "GET":
                continue
            clean_path = path.replace(":id", next(iter([client.get(MEALS).json()["meals"][0]["id"]]), ""))
            headers = user["headers"] if requires_auth else {}
            r = client.get(clean_path, headers=headers)
            if r.status_code >= 500:
                failures.append((method, path, r.status_code))
        assert failures == [], f"Endpoints returned 5xx: {failures}"
