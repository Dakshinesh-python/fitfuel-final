/// Dart model classes mirroring the backend's Prisma schema shapes.
/// Keep these in sync with the backend's `schema.prisma` as it evolves.

enum ActivityLevel { sedentary, light, moderate, active, extraActive }

enum FitnessGoal { weightLoss, muscleGain, weightGain, maintenance }

enum DietaryPreference { vegetarian, nonVegetarian, vegan }

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
  final int? calorieTarget;
  final int? proteinTargetG;
  final int? carbsTargetG;
  final int? fatTargetG;
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
    this.carbsTargetG,
    this.fatTargetG,
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
        calorieTarget: json['calorieTarget'] as int?,
        proteinTargetG: json['proteinTargetG'] as int?,
        carbsTargetG: json['carbsTargetG'] as int?,
        fatTargetG: json['fatTargetG'] as int?,
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
        'carbsTargetG': carbsTargetG,
        'fatTargetG': fatTargetG,
        'aiExplanation': aiExplanation,
      };
}

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
  final int matchScore;

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
    required this.matchScore,
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
        matchScore: json['matchScore'] as int,
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
        'matchScore': matchScore,
      };
}

class Order {
  final String id;
  final String mealId;
  final String platform; // 'swiggy' | 'zomato'
  final String deepLink;
  final DateTime createdAt;

  Order({
    required this.id,
    required this.mealId,
    required this.platform,
    required this.deepLink,
    required this.createdAt,
  });

  factory Order.fromJson(Map<String, dynamic> json) => Order(
        id: json['id'] as String,
        mealId: json['mealId'] as String,
        platform: json['platform'] as String,
        deepLink: json['deepLink'] as String,
        createdAt: DateTime.parse(json['createdAt'] as String),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'mealId': mealId,
        'platform': platform,
        'deepLink': deepLink,
        'createdAt': createdAt.toIso8601String(),
      };
}

class ProgressLog {
  final String id;
  final double weightKg;
  final int? caloriesConsumed;
  final int? proteinConsumedG;
  final int? carbsConsumedG;
  final int? fatConsumedG;
  final String? notes;
  final DateTime loggedAt;

  ProgressLog({
    required this.id,
    required this.weightKg,
    this.caloriesConsumed,
    this.proteinConsumedG,
    this.carbsConsumedG,
    this.fatConsumedG,
    this.notes,
    required this.loggedAt,
  });

  factory ProgressLog.fromJson(Map<String, dynamic> json) => ProgressLog(
        id: json['id'] as String,
        weightKg: (json['weightKg'] as num).toDouble(),
        caloriesConsumed: json['caloriesConsumed'] as int?,
        proteinConsumedG: json['proteinConsumedG'] as int?,
        carbsConsumedG: json['carbsConsumedG'] as int?,
        fatConsumedG: json['fatConsumedG'] as int?,
        notes: json['notes'] as String?,
        loggedAt: DateTime.parse(json['loggedAt'] as String),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'weightKg': weightKg,
        'caloriesConsumed': caloriesConsumed,
        'proteinConsumedG': proteinConsumedG,
        'carbsConsumedG': carbsConsumedG,
        'fatConsumedG': fatConsumedG,
        'notes': notes,
        'loggedAt': loggedAt.toIso8601String(),
      };
}
