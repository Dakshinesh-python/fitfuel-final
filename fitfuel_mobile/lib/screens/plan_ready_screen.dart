import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class PlanReadyScreen extends StatelessWidget {
  const PlanReadyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final args =
        ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
    final targets = args?['targets'] as Map<String, dynamic>?;
    final explanation = args?['explanation'] as String?;

    final calorieTarget =
        (targets?['calorieTarget'] as num?)?.round().toString() ?? '2,450';
    final bmi = (targets?['bmi'] as num?)?.toStringAsFixed(1) ?? '23.4';

    final proteinTargetG =
        (targets?['proteinTargetG'] as num?)?.toDouble() ?? 180.0;
    final carbTargetG = (targets?['carbTargetG'] as num?)?.toDouble() ?? 250.0;
    final fatTargetG = (targets?['fatTargetG'] as num?)?.toDouble() ?? 80.0;

    final proteinStr = proteinTargetG.round().toString();
    final carbsStr = carbTargetG.round().toString();
    final fatStr = fatTargetG.round().toString();

    final totalG = proteinTargetG + carbTargetG + fatTargetG;
    final proteinProgress = totalG > 0 ? proteinTargetG / totalG : 0.40;
    final carbsProgress = totalG > 0 ? carbTargetG / totalG : 0.45;
    final fatProgress = totalG > 0 ? fatTargetG / totalG : 0.15;

    final defaultExplanation =
        "Based on your goal to build lean muscle while maintaining low body fat, we've prioritized a moderate caloric surplus heavily weighted towards high-quality proteins and complex carbohydrates.";
    final displayExplanation = explanation ?? defaultExplanation;

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.marginMobile, vertical: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 64,
                  height: 64,
                  decoration: const BoxDecoration(
                      color: AppColors.primary, shape: BoxShape.circle),
                  child: const Icon(Icons.check_circle,
                      color: Colors.white, size: 32),
                ),
              ),
              const SizedBox(height: 16),
              Text('Your Plan is Ready',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.headlineLgMobile),
              const SizedBox(height: 8),
              Text(
                  "We've analyzed your data and crafted a personalized nutrition strategy to help you reach your goals optimally.",
                  textAlign: TextAlign.center,
                  style: AppTextStyles.bodyMd
                      .copyWith(color: AppColors.onSurfaceVariant)),
              const SizedBox(height: 28),
              Row(
                children: [
                  Expanded(
                    flex: 3,
                    child: AppCard(
                      radius: 20,
                      child: Column(
                        children: [
                          Text('Daily Calorie Target',
                              style: AppTextStyles.labelMd
                                  .copyWith(color: AppColors.onSurfaceVariant)),
                          const SizedBox(height: 12),
                          MacroRing(
                            progress: 0.85,
                            color: AppColors.primary,
                            size: 120,
                            center: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(calorieTarget,
                                    style: AppTextStyles.headlineMd
                                        .copyWith(fontSize: 22)),
                                Text('kcal / day',
                                    style: AppTextStyles.labelSm.copyWith(
                                        color: AppColors.onSurfaceVariant)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: AppCard(
                      radius: 20,
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text('Current BMI',
                              style: AppTextStyles.labelMd
                                  .copyWith(color: AppColors.onSurfaceVariant)),
                          const SizedBox(height: 12),
                          Text(bmi,
                              style: AppTextStyles.headlineLg
                                  .copyWith(fontSize: 30)),
                          const SizedBox(height: 4),
                          Text('Healthy Weight',
                              textAlign: TextAlign.center,
                              style: AppTextStyles.labelSm
                                  .copyWith(color: AppColors.primary)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.primaryContainer.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(AppRadius.lg),
                  border:
                      Border.all(color: AppColors.primary.withOpacity(0.25)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.auto_awesome,
                        color: AppColors.primary, size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('FitFuel AI Insight',
                              style: AppTextStyles.labelMd.copyWith(
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.w700)),
                          const SizedBox(height: 4),
                          Text(displayExplanation,
                              style: AppTextStyles.labelMd
                                  .copyWith(color: AppColors.onSurfaceVariant)),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _MacroStat(
                      icon: Icons.fitness_center,
                      label: 'Protein',
                      value: proteinStr,
                      unit: 'g',
                      progress: proteinProgress,
                      color: AppColors.primary),
                  _MacroStat(
                      icon: Icons.grass,
                      label: 'Carbs',
                      value: carbsStr,
                      unit: 'g',
                      progress: carbsProgress,
                      color: AppColors.secondaryContainer),
                  _MacroStat(
                      icon: Icons.water_drop,
                      label: 'Fats',
                      value: fatStr,
                      unit: 'g',
                      progress: fatProgress,
                      color: AppColors.tertiaryContainer),
                ],
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: () =>
                    Navigator.of(context).pushReplacementNamed('/dashboard'),
                style: ElevatedButton.styleFrom(
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(AppRadius.full))),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('Continue to Dashboard'),
                    SizedBox(width: 8),
                    Icon(Icons.arrow_forward, size: 18),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MacroStat extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final String unit;
  final double progress;
  final Color color;
  const _MacroStat({
    required this.icon,
    required this.label,
    required this.value,
    required this.unit,
    required this.progress,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        MacroRing(
          progress: progress,
          color: color,
          size: 68,
          center: Icon(icon, color: color, size: 20),
        ),
        const SizedBox(height: 8),
        Text(label, style: AppTextStyles.labelMd),
        Text('$value$unit',
            style: AppTextStyles.headlineMd.copyWith(fontSize: 16)),
      ],
    );
  }
}
