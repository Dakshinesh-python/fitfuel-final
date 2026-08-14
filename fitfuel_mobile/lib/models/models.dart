// Dart model classes mirroring the backend's Prisma schema shapes.
// Keep these in sync with the backend's `schema.prisma` as it evolves.
//
// INTEGRATION NOTE: Several fields were corrected during integration audit:
//   - ActivityLevel.veryActive (was extraActive — backend uses VERY_ACTIVE)
//   - HealthProfile.carbTargetG (was carbsTargetG — backend uses carbTargetG)
//   - ProgressLog.weightKg is nullable (backend allows weight-only or calorie-only logs)
//   - ProgressLog date field is 'date' in the backend JSON (was loggedAt)
//   - Order model: deepLink is a top-level field on the POST response, not on the order row
//   - Added Recommendation, ProgressSummary, WeightHistoryEntry models for frontend use

// ─── Enums ─────────────────────────────────────────────────────────────────

/// Matches backend's ActivityLevel enum (SEDENTARY, LIGHT, MODERATE, ACTIVE, VERY_ACTIVE)
enum ActivityLevel { sedentary, light, moderate, active, veryActive }

/// Matches backend's FitnessGoal enum
enum FitnessGoal { weightLoss, muscleGain, weightGain, maintenance }

/// Matches backend's DietaryPreference enum
enum DietaryPreference { vegetarian, nonVegetarian, vegan }

// ─── Auth ──────────────────────────────────────────────────────────────────

class User {
  final String id;
  final String name;
  final String email;
  final int? age;
  final String? gender;
  final double? heightCm;
  final double? weightKg;

  User({
    required this.id,
    required this.name,
    required this.email,
    this.age,
    this.gender,
    this.heightCm,
    this.weightKg,
  });

  factory User.fromJson(Map<String, dynamic> json) => User(
        id: json['id'] as String,
        name: json['name'] as String,
        email: json['email'] as String,
        age: json['age'] as int?,
        gender: json['gender'] as String?,
        heightCm: (json['heightCm'] as num?)?.toDouble(),
        weightKg: (json['weightKg'] as num?)?.toDouble(),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'email': email,
        'age': age,
        'gender': gender,
        'heightCm': heightCm,
        'weightKg': weightKg,
      };
}

// ─── Health Profile ─────────────────────────────────────────────────────────

/// Raw HealthProfile row (GET /api/health-profile → { profile: HealthProfile })
class HealthProfile {
  final String id;
  final String userId;
  final double currentWeightKg;
  final double targetWeightKg;
  final String activityLevel;
  final String fitnessGoal;
  final String dietaryPreference;
  final List<String> allergies;
  final double dailyBudget;
  final double? calorieTarget;
  final double? proteinTargetG;
  final int? carbTargetG; // NOTE: 'carbTargetG' not 'carbsTargetG'
  final double? fatTargetG;
  final double? bmi;
  final double? bmr;
  final double? tdee;
  final String? aiExplanation;

  HealthProfile({
    required this.id,
    required this.userId,
    required this.currentWeightKg,
    required this.targetWeightKg,
    required this.activityLevel,
    required this.fitnessGoal,
    required this.dietaryPreference,
    required this.allergies,
    required this.dailyBudget,
    this.calorieTarget,
    this.proteinTargetG,
    this.carbTargetG,
    this.fatTargetG,
    this.bmi,
    this.bmr,
    this.tdee,
    this.aiExplanation,
  });

  factory HealthProfile.fromJson(Map<String, dynamic> json) => HealthProfile(
        id: json['id'] as String,
        userId: json['userId'] as String,
        currentWeightKg: (json['currentWeightKg'] as num).toDouble(),
        targetWeightKg: (json['targetWeightKg'] as num).toDouble(),
        activityLevel: json['activityLevel'] as String,
        fitnessGoal: json['fitnessGoal'] as String,
        dietaryPreference: json['dietaryPreference'] as String,
        allergies: (json['allergies'] as List?)?.cast<String>() ?? const [],
        dailyBudget: (json['dailyBudget'] as num).toDouble(),
        calorieTarget: (json['calorieTarget'] as num?)?.toDouble(),
        proteinTargetG: (json['proteinTargetG'] as num?)?.toDouble(),
        carbTargetG:
            (json['carbTargetG'] as num?)?.toInt(), // key: 'carbTargetG'
        fatTargetG: (json['fatTargetG'] as num?)?.toDouble(),
        bmi: (json['bmi'] as num?)?.toDouble(),
        bmr: (json['bmr'] as num?)?.toDouble(),
        tdee: (json['tdee'] as num?)?.toDouble(),
        aiExplanation: json['aiExplanation'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'userId': userId,
        'currentWeightKg': currentWeightKg,
        'targetWeightKg': targetWeightKg,
        'activityLevel': activityLevel,
        'fitnessGoal': fitnessGoal,
        'dietaryPreference': dietaryPreference,
        'allergies': allergies,
        'dailyBudget': dailyBudget,
        'calorieTarget': calorieTarget,
        'proteinTargetG': proteinTargetG,
        'carbTargetG': carbTargetG,
        'fatTargetG': fatTargetG,
        'bmi': bmi,
        'bmr': bmr,
        'tdee': tdee,
        'aiExplanation': aiExplanation,
      };
}

/// NutritionTargets — returned under the 'targets' key in POST /api/health-profile response
class NutritionTargets {
  final double bmi;
  final String bmiCategory;
  final int bmr;
  final int tdee;
  final int calorieTarget;
  final int proteinTargetG;
  final int carbTargetG;
  final int fatTargetG;

  NutritionTargets({
    required this.bmi,
    required this.bmiCategory,
    required this.bmr,
    required this.tdee,
    required this.calorieTarget,
    required this.proteinTargetG,
    required this.carbTargetG,
    required this.fatTargetG,
  });

  factory NutritionTargets.fromJson(Map<String, dynamic> json) =>
      NutritionTargets(
        bmi: (json['bmi'] as num).toDouble(),
        bmiCategory: json['bmiCategory'] as String,
        bmr: (json['bmr'] as num).toInt(),
        tdee: (json['tdee'] as num).toInt(),
        calorieTarget: (json['calorieTarget'] as num).toInt(),
        proteinTargetG: (json['proteinTargetG'] as num).toInt(),
        carbTargetG: (json['carbTargetG'] as num).toInt(),
        fatTargetG: (json['fatTargetG'] as num).toInt(),
      );
}

// ─── Meals ─────────────────────────────────────────────────────────────────

class Meal {
  final String id;
  final String name;
  final String restaurant;
  final String cuisine;
  final String mealType;
  final double price;
  final int calories;
  final int proteinG;
  final int carbsG;
  final int fatG;
  final int healthScore;
  final String platform;
  final bool isVegetarian;
  final bool isVegan;
  final List<String> allergens;
  final String? imageUrl; // optional: Unsplash CDN URL; null = show placeholder

  Meal({
    required this.id,
    required this.name,
    required this.restaurant,
    required this.cuisine,
    required this.mealType,
    required this.price,
    required this.calories,
    required this.proteinG,
    required this.carbsG,
    required this.fatG,
    required this.healthScore,
    required this.platform,
    required this.isVegetarian,
    required this.isVegan,
    required this.allergens,
    this.imageUrl,
  });

  factory Meal.fromJson(Map<String, dynamic> json) => Meal(
        id: json['id'] as String,
        name: json['name'] as String,
        restaurant: json['restaurant'] as String,
        cuisine: json['cuisine'] as String,
        mealType: json['mealType'] as String,
        price: (json['price'] as num).toDouble(),
        calories: json['calories'] as int,
        proteinG: json['proteinG'] as int,
        carbsG: json['carbsG'] as int,
        fatG: json['fatG'] as int,
        healthScore: json['healthScore'] as int,
        platform: json['platform'] as String,
        isVegetarian: json['isVegetarian'] as bool? ?? false,
        isVegan: json['isVegan'] as bool? ?? false,
        allergens: (json['allergens'] as List?)?.cast<String>() ?? const [],
        imageUrl:
            json['imageUrl'] as String?, // nullable — backend field is String?
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'restaurant': restaurant,
        'cuisine': cuisine,
        'mealType': mealType,
        'price': price,
        'calories': calories,
        'proteinG': proteinG,
        'carbsG': carbsG,
        'fatG': fatG,
        'healthScore': healthScore,
        'platform': platform,
        'isVegetarian': isVegetarian,
        'isVegan': isVegan,
        'allergens': allergens,
        'imageUrl': imageUrl,
      };
}

/// Score breakdown from the recommendation engine
class MatchBreakdown {
  final double calorieAccuracy;
  final double proteinQuality;
  final double budgetFit;
  final double healthScore;

  MatchBreakdown({
    required this.calorieAccuracy,
    required this.proteinQuality,
    required this.budgetFit,
    required this.healthScore,
  });

  factory MatchBreakdown.fromJson(Map<String, dynamic> json) => MatchBreakdown(
        calorieAccuracy: (json['calorieAccuracy'] as num).toDouble(),
        proteinQuality: (json['proteinQuality'] as num).toDouble(),
        budgetFit: (json['budgetFit'] as num).toDouble(),
        healthScore: (json['healthScore'] as num).toDouble(),
      );
}

/// A single recommendation item — GET /api/recommendations returns { recommendations: [...] }
class Recommendation {
  final String mealId;
  final double score;
  final MatchBreakdown breakdown;
  final Meal meal;

  Recommendation({
    required this.mealId,
    required this.score,
    required this.breakdown,
    required this.meal,
  });

  factory Recommendation.fromJson(Map<String, dynamic> json) => Recommendation(
        mealId: json['mealId'] as String,
        score: (json['score'] as num).toDouble(),
        breakdown:
            MatchBreakdown.fromJson(json['breakdown'] as Map<String, dynamic>),
        meal: Meal.fromJson(json['meal'] as Map<String, dynamic>),
      );
}

// ─── Orders ────────────────────────────────────────────────────────────────

/// POST /api/orders returns { order: {...}, deepLink: "https://..." }
/// deepLink is a TOP-LEVEL field on the response — not on the order sub-object.
class OrderResult {
  final String orderId;
  final String platform;
  final String status;
  final String deepLink; // the Swiggy/Zomato search URL to open

  OrderResult({
    required this.orderId,
    required this.platform,
    required this.status,
    required this.deepLink,
  });

  factory OrderResult.fromJson(Map<String, dynamic> json) {
    final order = json['order'] as Map<String, dynamic>;
    return OrderResult(
      orderId: order['id'] as String,
      platform: order['platform'] as String,
      status: order['status'] as String,
      deepLink: json['deepLink'] as String, // top-level, not nested in order
    );
  }
}

// ─── Progress ──────────────────────────────────────────────────────────────

/// A single progress log entry.
/// NOTE: 'weightKg' is nullable because a log can record only calories (no weight).
/// NOTE: the date field in the JSON response is 'date' (not 'loggedAt').
class ProgressLog {
  final String id;
  final double? weightKg; // nullable — log may be calories-only
  final int? caloriesConsumed;
  final int? proteinConsumedG;
  final int? carbsConsumedG;
  final int? fatConsumedG;
  final String? notes;
  final DateTime date; // backend field name: 'date'

  ProgressLog({
    required this.id,
    this.weightKg,
    this.caloriesConsumed,
    this.proteinConsumedG,
    this.carbsConsumedG,
    this.fatConsumedG,
    this.notes,
    required this.date,
  });

  factory ProgressLog.fromJson(Map<String, dynamic> json) => ProgressLog(
        id: json['id'] as String,
        weightKg: (json['weightKg'] as num?)?.toDouble(),
        caloriesConsumed: json['caloriesConsumed'] as int?,
        proteinConsumedG: json['proteinConsumedG'] as int?,
        carbsConsumedG: json['carbsConsumedG'] as int?,
        fatConsumedG: json['fatConsumedG'] as int?,
        notes: json['notes'] as String?,
        date: DateTime.parse(
            json['date'] as String), // key: 'date' not 'loggedAt'
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'weightKg': weightKg,
        'caloriesConsumed': caloriesConsumed,
        'proteinConsumedG': proteinConsumedG,
        'carbsConsumedG': carbsConsumedG,
        'fatConsumedG': fatConsumedG,
        'notes': notes,
        'date': date.toIso8601String(),
      };
}

/// GET /api/progress/summary response
class ProgressSummary {
  final double weeklyAverageCalories;

  /// Percentage (0-100), capped at 100. Null when no health profile or no logs this week.
  final double? goalAchievementPct;

  ProgressSummary({
    required this.weeklyAverageCalories,
    this.goalAchievementPct,
  });

  factory ProgressSummary.fromJson(Map<String, dynamic> json) =>
      ProgressSummary(
        weeklyAverageCalories:
            (json['weeklyAverageCalories'] as num?)?.toDouble() ?? 0,
        goalAchievementPct: (json['goalAchievementPct'] as num?)?.toDouble(),
      );
}

/// A single { date, weightKg } pair from GET /api/progress/weight-history
class WeightHistoryEntry {
  final DateTime date;
  final double weightKg;

  WeightHistoryEntry({required this.date, required this.weightKg});

  factory WeightHistoryEntry.fromJson(Map<String, dynamic> json) =>
      WeightHistoryEntry(
        date: DateTime.parse(json['date'] as String),
        weightKg: (json['weightKg'] as num).toDouble(),
      );
}

// ─── Meal Plan ──────────────────────────────────────────────────────────────

/// A single item in a weekly meal plan.
/// GET /api/meal-plans/current → { mealPlan: { id, items: [...] } }
class MealPlanItem {
  final String id;
  final int dayOfWeek; // 0=Mon … 6=Sun (matches backend dayOfWeek)
  final String mealType; // 'BREAKFAST' | 'LUNCH' | 'SNACK' | 'DINNER'
  final double matchScore;
  final Meal meal;

  MealPlanItem({
    required this.id,
    required this.dayOfWeek,
    required this.mealType,
    required this.matchScore,
    required this.meal,
  });

  factory MealPlanItem.fromJson(Map<String, dynamic> json) => MealPlanItem(
        id: json['id'] as String,
        dayOfWeek: json['dayOfWeek'] as int,
        mealType: json['mealType'] as String,
        matchScore: (json['matchScore'] as num).toDouble(),
        meal: Meal.fromJson(json['meal'] as Map<String, dynamic>),
      );
}

/// The full weekly meal plan.
class MealPlan {
  final String id;
  final List<MealPlanItem> items;

  MealPlan({required this.id, required this.items});

  factory MealPlan.fromJson(Map<String, dynamic> json) => MealPlan(
        id: json['id'] as String,
        items: (json['items'] as List)
            .map((e) => MealPlanItem.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
