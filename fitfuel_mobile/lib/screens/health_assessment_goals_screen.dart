import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class HealthAssessmentGoalsScreen extends StatefulWidget {
  const HealthAssessmentGoalsScreen({super.key});

  @override
  State<HealthAssessmentGoalsScreen> createState() =>
      _HealthAssessmentGoalsScreenState();
}

class _HealthAssessmentGoalsScreenState
    extends State<HealthAssessmentGoalsScreen> {
  String _selected = 'WEIGHT_LOSS';

  static const _goals = [
    ('WEIGHT_LOSS', 'Weight Loss',
        'Burn fat and lean out safely and sustainably.', Icons.trending_down),
    ('MUSCLE_GAIN', 'Muscle Gain',
        'Build strength, size, and powerful functionality.',
        Icons.fitness_center),
    ('WEIGHT_GAIN', 'Weight Gain',
        'Increase mass healthily with proper nutrition.', Icons.trending_up),
    ('MAINTENANCE', 'Maintenance',
        'Maintain current weight while improving overall health.',
        Icons.balance),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: FitFuelAppBar(
        title: 'Step 3 of 4',
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pushNamed('/health-prefs'),
            child: Text('Skip',
                style: AppTextStyles.labelMd.copyWith(color: AppColors.primary)),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.marginMobile, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const StepProgressBar(currentStep: 3, totalSteps: 4),
              const SizedBox(height: 32),
              Text('What is your primary goal?',
                  style: AppTextStyles.headlineLgMobile),
              const SizedBox(height: 8),
              Text(
                  "Select the focus that best describes what you want to achieve. We'll tailor your plan accordingly.",
                  style: AppTextStyles.bodyMd
                      .copyWith(color: AppColors.onSurfaceVariant)),
              const SizedBox(height: 24),
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 16,
                crossAxisSpacing: 16,
                childAspectRatio: 0.85,
                children: _goals.map((g) {
                  final (key, title, desc, icon) = g;
                  final selected = _selected == key;
                  return GestureDetector(
                    onTap: () => setState(() => _selected = key),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 150),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: selected
                            ? AppColors.primaryContainer.withOpacity(0.1)
                            : Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: selected
                              ? AppColors.primary
                              : AppColors.outlineVariant.withOpacity(0.3),
                          width: selected ? 1.5 : 1,
                        ),
                        boxShadow: kCardShadowLevel1,
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Container(
                                width: 40,
                                height: 40,
                                decoration: BoxDecoration(
                                  color: selected
                                      ? AppColors.primary
                                      : AppColors.surfaceContainer,
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(icon,
                                    size: 20,
                                    color: selected
                                        ? Colors.white
                                        : AppColors.onSurfaceVariant),
                              ),
                              if (selected)
                                const Icon(Icons.check_circle,
                                    color: AppColors.primary, size: 20),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text(title,
                              style: AppTextStyles.headlineMd
                                  .copyWith(fontSize: 18)),
                          const SizedBox(height: 6),
                          Expanded(
                            child: Text(desc,
                                style: AppTextStyles.labelMd.copyWith(
                                    color: AppColors.onSurfaceVariant)),
                          ),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: () =>
                    Navigator.of(context).pushNamed('/health-prefs'),
                style: ElevatedButton.styleFrom(
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(AppRadius.full))),
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('Continue'),
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
