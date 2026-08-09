import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class HealthAssessmentActivityScreen extends StatefulWidget {
  const HealthAssessmentActivityScreen({super.key});

  @override
  State<HealthAssessmentActivityScreen> createState() =>
      _HealthAssessmentActivityScreenState();
}

class _ActivityOption {
  final String key;
  final String title;
  final String desc;
  final String multiplier;
  final IconData icon;
  const _ActivityOption(
      this.key, this.title, this.desc, this.multiplier, this.icon);
}

class _HealthAssessmentActivityScreenState
    extends State<HealthAssessmentActivityScreen> {
  String _selected = 'moderate';

  static const _options = [
    _ActivityOption('sedentary', 'Sedentary',
        'Little to no exercise. Mostly desk work or resting.', '1.2',
        Icons.chair_outlined),
    _ActivityOption('light', 'Lightly Active',
        'Light exercise or sports 1-3 days a week. E.g., walking.', '1.375',
        Icons.directions_walk),
    _ActivityOption('moderate', 'Moderately Active',
        'Moderate exercise or sports 3-5 days a week.', '1.55',
        Icons.fitness_center),
    _ActivityOption('active', 'Very Active',
        'Hard exercise or sports 6-7 days a week.', '1.725', Icons.pool),
    _ActivityOption(
        'extra_active',
        'Extra Active',
        'Very hard exercise, physical job, or training twice a day.',
        '1.9',
        Icons.directions_run),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: const FitFuelAppBar(title: 'FitFuel'),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.marginMobile, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('STEP 2 OF 4',
                      style: AppTextStyles.labelSm
                          .copyWith(color: AppColors.primary)),
                  Text('50% Completed',
                      style: AppTextStyles.labelSm
                          .copyWith(color: AppColors.onSurfaceVariant)),
                ],
              ),
              const SizedBox(height: 8),
              const StepProgressBar(currentStep: 2, totalSteps: 4),
              const SizedBox(height: 32),
              Text("What's your daily activity level?",
                  style: AppTextStyles.headlineLgMobile),
              const SizedBox(height: 12),
              Text(
                  'This helps us calculate your baseline metabolic rate and daily calorie needs.',
                  style: AppTextStyles.bodyLg
                      .copyWith(color: AppColors.onSurfaceVariant)),
              const SizedBox(height: 24),
              ..._options.map((o) {
                final selected = _selected == o.key;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: GestureDetector(
                    onTap: () => setState(() => _selected = o.key),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 150),
                      padding: const EdgeInsets.all(20),
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
                          Container(
                            width: 48,
                            height: 48,
                            decoration: BoxDecoration(
                              color: selected
                                  ? AppColors.primary
                                  : AppColors.surfaceContainer,
                              shape: BoxShape.circle,
                            ),
                            child: Icon(o.icon,
                                color: selected
                                    ? Colors.white
                                    : AppColors.onSurfaceVariant),
                          ),
                          const SizedBox(height: 16),
                          Text(o.title, style: AppTextStyles.headlineMd),
                          const SizedBox(height: 8),
                          Text(o.desc,
                              style: AppTextStyles.bodyMd.copyWith(
                                  color: AppColors.onSurfaceVariant)),
                          const SizedBox(height: 16),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 12, vertical: 4),
                                decoration: BoxDecoration(
                                  color: selected
                                      ? AppColors.primary.withOpacity(0.1)
                                      : AppColors.surfaceContainerLow,
                                  borderRadius:
                                      BorderRadius.circular(AppRadius.full),
                                ),
                                child: Text('Multiplier: ${o.multiplier}',
                                    style: AppTextStyles.labelSm.copyWith(
                                        color: selected
                                            ? AppColors.primary
                                            : AppColors.outline)),
                              ),
                              if (selected)
                                const Icon(Icons.check_circle,
                                    color: AppColors.primary),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              }),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () =>
                          Navigator.of(context).pushNamed('/health-goals'),
                      style: OutlinedButton.styleFrom(
                          shape: RoundedRectangleBorder(
                              borderRadius:
                                  BorderRadius.circular(AppRadius.full))),
                      child: const Text('Skip for now'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () =>
                          Navigator.of(context).pushNamed('/health-goals'),
                      style: ElevatedButton.styleFrom(
                          shape: RoundedRectangleBorder(
                              borderRadius:
                                  BorderRadius.circular(AppRadius.full))),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text('Continue'),
                          SizedBox(width: 8),
                          Icon(Icons.arrow_forward, size: 18),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
