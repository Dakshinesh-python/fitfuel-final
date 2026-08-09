import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'services/auth_service.dart';
import 'screens/splash_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/health_assessment_weight_screen.dart';
import 'screens/health_assessment_activity_screen.dart';
import 'screens/health_assessment_goals_screen.dart';
import 'screens/health_assessment_prefs_screen.dart';
import 'screens/plan_ready_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/recommendations_screen.dart';
import 'screens/meal_detail_screen.dart';
import 'screens/weekly_meal_plan_screen.dart';
import 'screens/progress_screen.dart';

void main() {
  runApp(const FitFuelApp());
}

class FitFuelApp extends StatelessWidget {
  const FitFuelApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FitFuel',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      initialRoute: '/',
      routes: {
        '/': (context) => const SplashScreen(),
        '/onboarding': (context) => const OnboardingScreen(),
        '/login': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/health-weight': (context) => const HealthAssessmentWeightScreen(),
        '/health-activity': (context) => const HealthAssessmentActivityScreen(),
        '/health-goals': (context) => const HealthAssessmentGoalsScreen(),
        '/health-prefs': (context) => const HealthAssessmentPrefsScreen(),
        '/plan-ready': (context) => const PlanReadyScreen(),
        '/dashboard': (context) => const DashboardScreen(),
        '/recommendations': (context) => const RecommendationsScreen(),
        '/meal-detail': (context) => const MealDetailScreen(),
        '/weekly-plan': (context) => const WeeklyMealPlanScreen(),
        '/progress': (context) => const ProgressScreen(),
      },
    );
  }
}
