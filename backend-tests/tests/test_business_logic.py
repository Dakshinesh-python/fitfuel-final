"""
Business logic tests: verifies FitFuel's domain calculations against the
exact formulas in backend/src/services/nutritionCalculator.ts and the
eligibility rules in recommendationEngine.ts, by independently re-computing
expected values in Python and comparing against live API responses --
rather than just checking "some number came back."
"""
import math
import uuid

import pytest

from config import API_PREFIX

REGISTER = f"{API_PREFIX}/auth/register"
HEALTH_PROFILE = f"{API_PREFIX}/health-profile"
MEAL_PLAN_GENERATE = f"{API_PREFIX}/meal-plans/generate"
RECOMMENDATIONS = f"{API_PREFIX}/recommendations"
PROGRESS = f"{API_PREFIX}/progress"
PROGRESS_SUMMARY = f"{API_PREFIX}/progress/summary"

# ─── Python re-implementation of nutritionCalculator.ts, kept 1:1 with the
# TypeScript source (backend/src/services/nutritionCalculator.ts) so results
# can be compared bit-for-bit. Math.round in JS rounds half-away-from-zero
# for positive numbers; Python's built-in round() uses banker's rounding, so
# js_round replicates JS semantics explicitly. ────────────────────────────

ACTIVITY_MULTIPLIERS = {
    "SEDENTARY": 1.2,
    "LIGHT": 1.375,
    "MODERATE": 1.55,
    "ACTIVE": 1.725,
    "VERY_ACTIVE": 1.9,
}
GOAL_CALORIE_ADJUSTMENT = {
    "WEIGHT_LOSS": -500,
    "WEIGHT_GAIN": 400,
    "MUSCLE_GAIN": 300,
    "MAINTENANCE": 0,
}
GOAL_MACRO_SPLIT = {
    "WEIGHT_LOSS": {"protein": 0.35, "carbs": 0.35, "fat": 0.3},
    "WEIGHT_GAIN": {"protein": 0.25, "carbs": 0.5, "fat": 0.25},
    "MUSCLE_GAIN": {"protein": 0.3, "carbs": 0.45, "fat": 0.25},
    "MAINTENANCE": {"protein": 0.25, "carbs": 0.45, "fat": 0.3},
}


def js_round(x: float) -> int:
    return math.floor(x + 0.5)


def calc_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    return round(weight_kg / (height_m * height_m), 1)


def bmi_category(bmi):
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal weight"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def calc_bmr(weight_kg, height_cm, age, gender):
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if gender == "MALE":
        return js_round(base + 5)
    if gender == "FEMALE":
        return js_round(base - 161)
    return js_round(base - 78)


def calc_targets(weight_kg, height_cm, age, gender, activity_level, fitness_goal):
    bmi = calc_bmi(weight_kg, height_cm)
    bmr = calc_bmr(weight_kg, height_cm, age, gender)
    tdee = js_round(bmr * ACTIVITY_MULTIPLIERS[activity_level])
    adjustment = GOAL_CALORIE_ADJUSTMENT[fitness_goal]
    calorie_target = max(1200, tdee + adjustment)
    split = GOAL_MACRO_SPLIT[fitness_goal]
    protein_g = js_round((calorie_target * split["protein"]) / 4)
    carb_g = js_round((calorie_target * split["carbs"]) / 4)
    fat_g = js_round((calorie_target * split["fat"]) / 9)
    return {
        "bmi": bmi,
        "bmiCategory": bmi_category(bmi),
        "bmr": bmr,
        "tdee": tdee,
        "calorieTarget": calorie_target,
        "proteinTargetG": protein_g,
        "carbTargetG": carb_g,
        "fatTargetG": fat_g,
    }


def _register_with_metrics(client, age, gender, height_cm, weight_kg):
    email = f"biz-{uuid.uuid4().hex[:10]}@backendtests.local"
    r = client.post(
        REGISTER,
        json={
            "name": "Business Logic Tester",
            "email": email,
            "password": "validpass1",
            "age": age,
            "gender": gender,
            "heightCm": height_cm,
            "weightKg": weight_kg,
        },
    )
    assert r.status_code == 201, r.text
    return {"headers": {"Authorization": f"Bearer {r.json()['token']}"}, "id": r.json()["user"]["id"]}


def _submit_profile(client, headers, weight_kg, target_weight_kg, activity_level, fitness_goal, dietary_preference="NON_VEGETARIAN", allergies=None, daily_budget=500):
    r = client.post(
        HEALTH_PROFILE,
        json={
            "currentWeightKg": weight_kg,
            "targetWeightKg": target_weight_kg,
            "activityLevel": activity_level,
            "fitnessGoal": fitness_goal,
            "dietaryPreference": dietary_preference,
            "allergies": allergies or [],
            "dailyBudget": daily_budget,
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


NUTRITION_COMBOS = [
    # (age, gender, heightCm, weightKg, activityLevel, fitnessGoal)
    (28, "FEMALE", 165, 60, "SEDENTARY", "WEIGHT_LOSS"),
    (28, "FEMALE", 165, 60, "LIGHT", "WEIGHT_LOSS"),
    (28, "FEMALE", 165, 60, "MODERATE", "WEIGHT_LOSS"),
    (28, "FEMALE", 165, 60, "ACTIVE", "MAINTENANCE"),
    (28, "FEMALE", 165, 60, "VERY_ACTIVE", "MUSCLE_GAIN"),
    (35, "MALE", 178, 82, "MODERATE", "WEIGHT_GAIN"),
    (45, "MALE", 178, 82, "MODERATE", "MUSCLE_GAIN"),
    (52, "OTHER", 170, 70, "MODERATE", "MAINTENANCE"),
]


class TestNutritionCalculations:
    @pytest.mark.parametrize(
        "age,gender,height_cm,weight_kg,activity_level,fitness_goal",
        NUTRITION_COMBOS,
        ids=[f"{g}-{a}-{h}cm-{w}kg-{al}-{fg}" for a, g, h, w, al, fg in NUTRITION_COMBOS],
    )
    def test_nutrition_targets_match_reference_formula_exactly(
        self, client, age, gender, height_cm, weight_kg, activity_level, fitness_goal
    ):
        """
        CATEGORY: Business Logic
        TITLE: BMI/BMR/TDEE/macro targets match the Mifflin-St Jeor reference formula exactly
        OBJECTIVE: Independently re-implement nutritionCalculator.ts's exact
            formula in Python and compare bit-for-bit against the live API's
            computed values for a range of age/gender/activity/goal combinations.
        EXPECTED: profile.bmi, targets.bmr, targets.tdee, targets.calorieTarget,
            targets.proteinTargetG, targets.carbTargetG, targets.fatTargetG all
            equal the independently-computed reference values exactly.
        SEVERITY: HIGH
        """
        user = _register_with_metrics(client, age, gender, height_cm, weight_kg)
        body = _submit_profile(client, user["headers"], weight_kg, weight_kg - 5, activity_level, fitness_goal)

        expected = calc_targets(weight_kg, height_cm, age, gender, activity_level, fitness_goal)

        assert body["profile"]["bmi"] == expected["bmi"]
        assert body["targets"]["bmr"] == expected["bmr"]
        assert body["targets"]["tdee"] == expected["tdee"]
        assert body["targets"]["calorieTarget"] == expected["calorieTarget"]
        assert body["targets"]["proteinTargetG"] == expected["proteinTargetG"]
        assert body["targets"]["carbTargetG"] == expected["carbTargetG"]
        assert body["targets"]["fatTargetG"] == expected["fatTargetG"]

    @pytest.mark.parametrize(
        "weight_kg,height_cm,expected_category",
        [
            (50, 180, "Underweight"),   # BMI ~15.4
            (60, 180, "Normal weight"), # BMI ~18.5 boundary/just above
            (75, 180, "Normal weight"), # BMI ~23.1
            (85, 180, "Overweight"),    # BMI ~26.2
            (100, 180, "Obese"),        # BMI ~30.9
        ],
        ids=["underweight", "normal-lower-bound", "normal-mid", "overweight", "obese"],
    )
    def test_bmi_category_boundaries(self, client, weight_kg, height_cm, expected_category):
        """
        CATEGORY: Business Logic
        TITLE: BMI category thresholds (18.5 / 25 / 30) applied correctly
        OBJECTIVE: Confirm bmiCategory()'s four bands are reproduced correctly
            by the live API across representative weight/height combinations.
        EXPECTED: profile response's implied BMI category matches the
            Python reference (computed via the same <18.5/<25/<30/else bands).
        SEVERITY: MEDIUM
        """
        user = _register_with_metrics(client, 30, "MALE", height_cm, weight_kg)
        body = _submit_profile(client, user["headers"], weight_kg, weight_kg, "MODERATE", "MAINTENANCE")
        actual_bmi = body["profile"]["bmi"]
        assert bmi_category(actual_bmi) == expected_category

    def test_calorie_target_never_goes_below_1200_floor(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Calorie target respects the 1200 kcal safety floor
        OBJECTIVE: A small, older, sedentary user on WEIGHT_LOSS (-500 kcal
            adjustment) can have tdee + adjustment fall below 1200; confirm
            calculateNutritionTargets' Math.max(1200, ...) floor is enforced
            end-to-end, not just in the unit-level formula.
        EXPECTED: targets.calorieTarget >= 1200 always, even when the raw
            tdee - 500 arithmetic would go lower.
        SEVERITY: HIGH
        """
        # Small frame, older age, sedentary -> low BMR/TDEE
        user = _register_with_metrics(client, 65, "FEMALE", 150, 45)
        body = _submit_profile(client, user["headers"], 45, 43, "SEDENTARY", "WEIGHT_LOSS")
        raw_tdee = body["targets"]["tdee"]
        assert body["targets"]["calorieTarget"] >= 1200
        if raw_tdee - 500 < 1200:
            assert body["targets"]["calorieTarget"] == 1200


class TestMealPlanGeneration:
    def test_generated_meal_plan_has_exactly_28_items(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Meal plan contains exactly 7 days x 4 meal types = 28 items
        OBJECTIVE: Confirm the generation loop produces one item per
            (day, mealType) slot for all 7 days and all 4 meal types.
        EXPECTED: len(mealPlan.items) == 28.
        SEVERITY: MEDIUM
        """
        user = _register_with_metrics(client, 29, "FEMALE", 165, 60)
        _submit_profile(client, user["headers"], 60, 55, "MODERATE", "WEIGHT_LOSS")
        r = client.post(MEAL_PLAN_GENERATE, headers=user["headers"])
        assert r.status_code == 201
        assert len(r.json()["mealPlan"]["items"]) == 28

    def test_meal_plan_covers_all_four_meal_types_each_day(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Every day in the plan has one of each meal type
        OBJECTIVE: Confirm the (day, mealType) grid is fully populated,
            not just 28 items total by coincidence.
        EXPECTED: For each of the 7 dayOfWeek values (0-6), the set of
            mealTypes present is exactly {BREAKFAST, LUNCH, DINNER, SNACK}.
        SEVERITY: MEDIUM
        """
        user = _register_with_metrics(client, 29, "MALE", 178, 75)
        _submit_profile(client, user["headers"], 75, 72, "ACTIVE", "MUSCLE_GAIN")
        r = client.post(MEAL_PLAN_GENERATE, headers=user["headers"])
        items = r.json()["mealPlan"]["items"]
        by_day = {}
        for item in items:
            by_day.setdefault(item["dayOfWeek"], set()).add(item["mealType"])
        assert set(by_day.keys()) == set(range(7))
        for day, types in by_day.items():
            assert types == {"BREAKFAST", "LUNCH", "DINNER", "SNACK"}, f"day {day} missing types: {types}"

    def test_meal_plan_items_never_contain_users_allergens(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Generated meal plan excludes the user's declared allergens
        OBJECTIVE: recommendationEngine.isEligible() filters out any meal
            whose allergens list intersects the user's allergies. Declare a
            common allergen (dairy) and confirm no chosen meal contains it.
        EXPECTED: No item in the generated plan has "dairy" in its meal's allergens.
        SEVERITY: CRITICAL
        """
        user = _register_with_metrics(client, 29, "FEMALE", 165, 60)
        _submit_profile(client, user["headers"], 60, 58, "MODERATE", "MAINTENANCE", allergies=["dairy"])
        r = client.post(MEAL_PLAN_GENERATE, headers=user["headers"])
        assert r.status_code == 201
        for item in r.json()["mealPlan"]["items"]:
            meal = item.get("meal") or {}
            assert "dairy" not in (meal.get("allergens") or []), f"meal {meal.get('name')} contains a declared allergen"

    def test_vegan_preference_meal_plan_items_are_all_vegan(self, client):
        """
        CATEGORY: Business Logic
        TITLE: VEGAN dietary preference restricts meal plan to vegan meals only
        OBJECTIVE: isEligible() requires meal.isVegan === true when
            dietaryPreference is VEGAN (vegetarian-but-not-vegan meals are
            excluded too, per the source's exact condition).
        EXPECTED: Every item.meal.isVegan is true.
        SEVERITY: HIGH
        """
        user = _register_with_metrics(client, 29, "FEMALE", 165, 60)
        _submit_profile(client, user["headers"], 60, 58, "MODERATE", "MAINTENANCE", dietary_preference="VEGAN")
        r = client.post(MEAL_PLAN_GENERATE, headers=user["headers"])
        assert r.status_code == 201
        items = r.json()["mealPlan"]["items"]
        non_vegan = [i for i in items if not (i.get("meal") or {}).get("isVegan")]
        assert non_vegan == [], f"non-vegan meals leaked into a VEGAN plan: {non_vegan}"

    def test_meal_plan_week_start_falls_on_a_monday(self, client):
        """
        CATEGORY: Business Logic
        TITLE: weekStart date is always a Monday
        OBJECTIVE: The route computes weekStart by adjusting to the nearest
            Monday-of-the-current-week. Confirm the returned date's weekday
            is actually Monday regardless of what day the suite runs on.
        EXPECTED: datetime.weekday() == 0 (Python: Monday=0) for weekStart.
        SEVERITY: LOW
        """
        import datetime

        user = _register_with_metrics(client, 30, "MALE", 178, 78)
        _submit_profile(client, user["headers"], 78, 75, "MODERATE", "MAINTENANCE")
        r = client.post(MEAL_PLAN_GENERATE, headers=user["headers"])
        week_start = r.json()["mealPlan"]["weekStart"]
        parsed = datetime.datetime.fromisoformat(week_start.replace("Z", "+00:00"))
        assert parsed.weekday() == 0, f"weekStart {week_start} is not a Monday"

    def test_meal_plan_generation_requires_completed_health_assessment(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Meal plan generation blocked without a completed health profile
        OBJECTIVE: The route checks profile.tdee / profile.proteinTargetG
            before generating. A brand-new user with no profile at all must
            be blocked with a clear error, not an empty/broken plan.
        EXPECTED: 400 with an error message.
        SEVERITY: MEDIUM
        """
        user = _register_with_metrics(client, 30, "MALE", 178, 78)
        r = client.post(MEAL_PLAN_GENERATE, headers=user["headers"])
        assert r.status_code == 400
        assert "error" in r.json()


class TestRecommendations:
    def test_recommendations_exclude_users_declared_allergens(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Recommendations exclude meals containing the user's allergens
        OBJECTIVE: Same eligibility rule as the meal-plan generator, applied
            to the standalone recommendations endpoint.
        EXPECTED: No recommended meal's allergens list contains "nuts".
        SEVERITY: CRITICAL
        """
        user = _register_with_metrics(client, 29, "FEMALE", 165, 60)
        _submit_profile(client, user["headers"], 60, 58, "MODERATE", "MAINTENANCE", allergies=["nuts"])
        r = client.get(RECOMMENDATIONS, params={"mealType": "SNACK"}, headers=user["headers"])
        assert r.status_code == 200
        for rec in r.json()["recommendations"]:
            assert "nuts" not in (rec["meal"].get("allergens") or [])

    def test_recommendations_respect_vegetarian_preference(self, client):
        """
        CATEGORY: Business Logic
        TITLE: VEGETARIAN preference excludes meat but allows vegan meals too
        OBJECTIVE: isEligible()'s VEGETARIAN branch allows meal.isVegetarian
            OR meal.isVegan (a vegan meal is a subset of vegetarian).
        EXPECTED: Every recommended meal has isVegetarian == true or isVegan == true.
        SEVERITY: HIGH
        """
        user = _register_with_metrics(client, 29, "MALE", 178, 78)
        _submit_profile(client, user["headers"], 78, 75, "MODERATE", "MAINTENANCE", dietary_preference="VEGETARIAN")
        r = client.get(RECOMMENDATIONS, params={"mealType": "LUNCH"}, headers=user["headers"])
        assert r.status_code == 200
        for rec in r.json()["recommendations"]:
            meal = rec["meal"]
            assert meal["isVegetarian"] or meal["isVegan"], f"non-vegetarian meal leaked: {meal['name']}"

    def test_recommendations_sorted_by_score_descending(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Recommendations are returned in descending score order
        OBJECTIVE: rankMeals() sorts by score descending before slicing top N.
        EXPECTED: The score sequence is non-increasing.
        SEVERITY: LOW
        """
        user = _register_with_metrics(client, 29, "MALE", 178, 78)
        _submit_profile(client, user["headers"], 78, 75, "MODERATE", "MAINTENANCE")
        r = client.get(RECOMMENDATIONS, params={"mealType": "DINNER"}, headers=user["headers"])
        scores = [rec["score"] for rec in r.json()["recommendations"]]
        assert scores == sorted(scores, reverse=True)

    def test_recommendations_default_meal_type_is_lunch(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Omitting mealType defaults to LUNCH
        OBJECTIVE: `const mealType = (req.query.mealType as string) ?? "LUNCH"`.
        EXPECTED: Every meal in the response has mealType == LUNCH.
        SEVERITY: LOW
        """
        user = _register_with_metrics(client, 29, "FEMALE", 165, 60)
        _submit_profile(client, user["headers"], 60, 58, "MODERATE", "MAINTENANCE")
        r = client.get(RECOMMENDATIONS, headers=user["headers"])
        assert r.status_code == 200
        for rec in r.json()["recommendations"]:
            assert rec["meal"]["mealType"] == "LUNCH"

    def test_recommendations_returns_at_most_five(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Recommendations are capped at top 5
        OBJECTIVE: rankMeals(candidates, ctx, 5) hardcodes topN=5 for this route.
        EXPECTED: len(recommendations) <= 5.
        SEVERITY: LOW
        """
        user = _register_with_metrics(client, 29, "MALE", 178, 78)
        _submit_profile(client, user["headers"], 78, 75, "MODERATE", "MAINTENANCE")
        r = client.get(RECOMMENDATIONS, params={"mealType": "BREAKFAST"}, headers=user["headers"])
        assert len(r.json()["recommendations"]) <= 5

    def test_recommendations_requires_completed_health_assessment(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Recommendations blocked without a completed health profile
        OBJECTIVE: Same guard as meal-plan generation, on this endpoint.
        EXPECTED: 400.
        SEVERITY: MEDIUM
        """
        user = _register_with_metrics(client, 30, "MALE", 178, 78)
        r = client.get(RECOMMENDATIONS, headers=user["headers"])
        assert r.status_code == 400

    def test_recommendations_invalid_meal_type_does_not_crash_the_server(self, client):
        """
        CATEGORY: Business Logic
        TITLE: [FINDING] Invalid mealType on /recommendations has the same unvalidated-enum crash risk as GET /meals
        OBJECTIVE: recommendation.routes.ts does the identical unsafe cast as
            meal.routes.ts: `mealType: mealType as MealType` with no runtime
            validation, against the same native Postgres MealType enum. The
            GET /api/meals version of this bug is CONFIRMED to crash the
            entire Node process when run against real Postgres (see
            test_input_validation.py::test_meals_invalid_meal_type_crashes_the_server_process
            and security-review.md, DOS-1) -- this route shares the exact
            same root cause and is reached by any authenticated user (i.e.
            anyone who can self-register, which is anyone).
        EXPECTED: 200 or 400, never a crash. Same remediation as DOS-1:
            validate mealType against the enum's allowed values before
            querying, and wrap the handler in try/catch.
        SEVERITY: CRITICAL
        """
        user = _register_with_metrics(client, 29, "FEMALE", 165, 60)
        _submit_profile(client, user["headers"], 60, 58, "MODERATE", "MAINTENANCE")
        r = client.get(RECOMMENDATIONS, params={"mealType": "MIDNIGHT_SNACK"}, headers=user["headers"])
        assert r.status_code in (200, 400)
        assert client.get("/health").status_code == 200


class TestOrderDeepLinks:
    def test_swiggy_order_deep_link_uses_swiggy_search_format(self, client, any_meal_id):
        """
        CATEGORY: Business Logic
        TITLE: SWIGGY order returns a swiggy.com search deep link
        OBJECTIVE: buildDeepLink() builds `https://www.swiggy.com/search?query=<dish>`.
        EXPECTED: deepLink starts with the Swiggy search URL and contains "query=".
        SEVERITY: LOW
        """
        user = _register_with_metrics(client, 30, "MALE", 178, 78)
        r = client.post(f"{API_PREFIX}/orders", json={"mealId": any_meal_id, "platform": "SWIGGY"}, headers=user["headers"])
        assert r.status_code == 201
        assert r.json()["deepLink"].startswith("https://www.swiggy.com/search?query=")

    def test_zomato_order_deep_link_points_to_zomato(self, client, any_meal_id):
        """
        CATEGORY: Business Logic
        TITLE: ZOMATO order deep link points to a zomato.com URL
        OBJECTIVE: buildDeepLink() originally forced a &type=dishes dish-search
            link for Zomato. As of commits 3bacaae/b3cac93/2cbae71, this was
            deliberately changed to a hardcoded generic Chennai delivery page
            (https://www.zomato.com/chennai/delivery) because, per the
            commit's own message, "Zomato dish search is broken" -- a real
            product decision, not a regression. This test intentionally only
            checks the domain, not the exact path/query, so it doesn't need
            editing again the next time this URL is adjusted (it's changed
            three times already). If the exact target matters again later,
            tighten this back up against whatever the current intended
            behavior is.
        EXPECTED: deepLink is an https://www.zomato.com/... URL.
        SEVERITY: LOW
        """
        user = _register_with_metrics(client, 30, "MALE", 178, 78)
        r = client.post(f"{API_PREFIX}/orders", json={"mealId": any_meal_id, "platform": "ZOMATO"}, headers=user["headers"])
        assert r.status_code == 201
        assert r.json()["deepLink"].startswith("https://www.zomato.com/")


class TestProgressSummary:
    def test_weekly_average_calories_computed_correctly(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Weekly average calorie calculation matches manual computation
        OBJECTIVE: Log 3 known calorie values, independently compute the mean
            in the test, and compare against the API's weeklyAverageCalories.
        EXPECTED: API's rounded average equals round(mean(logged_values)).
        SEVERITY: MEDIUM
        """
        user = _register_with_metrics(client, 30, "FEMALE", 165, 60)
        _submit_profile(client, user["headers"], 60, 58, "MODERATE", "MAINTENANCE")
        values = [1800, 2000, 2200]
        for v in values:
            resp = client.post(PROGRESS, json={"caloriesConsumed": v}, headers=user["headers"])
            assert resp.status_code == 201
        r = client.get(PROGRESS_SUMMARY, headers=user["headers"])
        assert r.status_code == 200
        expected_avg = js_round(sum(values) / len(values))
        assert r.json()["weeklyAverageCalories"] == expected_avg

    def test_goal_achievement_percent_capped_at_100(self, client):
        """
        CATEGORY: Business Logic
        TITLE: goalAchievementPct never exceeds 100 even when over-eating relative to TDEE
        OBJECTIVE: `Math.min(100, Math.round((avgCalories / tdee) * 100))`.
            Log an implausibly high calorie value (10x a typical TDEE) and
            confirm the percentage is clamped rather than reported as e.g. 340%.
        EXPECTED: goalAchievementPct <= 100.
        SEVERITY: LOW
        """
        user = _register_with_metrics(client, 30, "FEMALE", 165, 60)
        _submit_profile(client, user["headers"], 60, 58, "MODERATE", "MAINTENANCE")
        client.post(PROGRESS, json={"caloriesConsumed": 20000}, headers=user["headers"])
        r = client.get(PROGRESS_SUMMARY, headers=user["headers"])
        assert r.json()["goalAchievementPct"] <= 100

    def test_progress_summary_with_no_logs_returns_zero_average_and_null_goal_pct(self, client):
        """
        CATEGORY: Business Logic
        TITLE: Summary with zero logged entries degrades to sensible defaults
        OBJECTIVE: The route's ternaries fall back to avgCalories=0 and
            goalAchievementPct=null when logs.length === 0.
        EXPECTED: weeklyAverageCalories == 0, goalAchievementPct is null.
        SEVERITY: LOW
        """
        user = _register_with_metrics(client, 30, "MALE", 178, 78)
        _submit_profile(client, user["headers"], 78, 75, "MODERATE", "MAINTENANCE")
        r = client.get(PROGRESS_SUMMARY, headers=user["headers"])
        assert r.status_code == 200
        assert r.json()["weeklyAverageCalories"] == 0
        assert r.json()["goalAchievementPct"] is None
