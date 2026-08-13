import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class HealthAssessmentPrefsScreen extends StatefulWidget {
  const HealthAssessmentPrefsScreen({super.key});

  @override
  State<HealthAssessmentPrefsScreen> createState() =>
      _HealthAssessmentPrefsScreenState();
}

class _HealthAssessmentPrefsScreenState
    extends State<HealthAssessmentPrefsScreen> {
  String _diet = 'VEGETARIAN';
  final Set<String> _allergies = {};
  double _budget = 45;

  static const _diets = [
    ('VEGETARIAN', 'Vegetarian', Icons.eco_outlined),
    ('NON_VEGETARIAN', 'Non-Vegetarian', Icons.set_meal_outlined),
    ('VEGAN', 'Vegan', Icons.spa_outlined),
  ];

  static const _allergyOptions = [
    'Dairy',
    'Egg',
    'Gluten',
    'Nuts',
    'Shellfish'
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
              Text('Dietary Details', style: AppTextStyles.headlineLgMobile),
              const SizedBox(height: 4),
              Text("Let's refine your recommendations.",
                  style: AppTextStyles.bodyMd
                      .copyWith(color: AppColors.onSurfaceVariant)),
              const SizedBox(height: 16),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Step 4 of 4', style: AppTextStyles.labelMd),
                ],
              ),
              const SizedBox(height: 8),
              const StepProgressBar(currentStep: 4, totalSteps: 4),
              const SizedBox(height: 32),
              Text('Dietary Preference',
                  style: AppTextStyles.headlineMd.copyWith(fontSize: 18)),
              const SizedBox(height: 12),
              Row(
                children: _diets.map((d) {
                  final (key, label, icon) = d;
                  final selected = _diet == key;
                  return Expanded(
                    child: Padding(
                      padding: EdgeInsets.only(
                          right: d == _diets.last ? 0 : 8),
                      child: GestureDetector(
                        onTap: () => setState(() => _diet = key),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 150),
                          padding: const EdgeInsets.symmetric(
                              vertical: 16, horizontal: 8),
                          decoration: BoxDecoration(
                            color: selected
                                ? AppColors.primaryContainer
                                    .withOpacity(0.12)
                                : Colors.white,
                            borderRadius: BorderRadius.circular(AppRadius.md),
                            border: Border.all(
                              color: selected
                                  ? AppColors.primary
                                  : AppColors.outlineVariant,
                              width: selected ? 1.5 : 1,
                            ),
                          ),
                          child: Column(
                            children: [
                              Icon(icon,
                                  color: selected
                                      ? AppColors.primary
                                      : AppColors.onSurfaceVariant),
                              const SizedBox(height: 8),
                              Text(label,
                                  textAlign: TextAlign.center,
                                  style: AppTextStyles.labelMd.copyWith(
                                      color: selected
                                          ? AppColors.primary
                                          : AppColors.onSurfaceVariant,
                                      fontWeight: FontWeight.w600)),
                            ],
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 28),
              Row(
                children: [
                  Text('Allergies & Restrictions',
                      style: AppTextStyles.headlineMd.copyWith(fontSize: 18)),
                  const SizedBox(width: 8),
                  Text('Optional',
                      style: AppTextStyles.labelSm
                          .copyWith(color: AppColors.outline)),
                ],
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: _allergyOptions.map((a) {
                  final selected = _allergies.contains(a);
                  return SelectableChip(
                    label: a,
                    selected: selected,
                    onTap: () => setState(() {
                      if (selected) {
                        _allergies.remove(a);
                      } else {
                        _allergies.add(a);
                      }
                    }),
                  );
                }).toList(),
              ),
              const SizedBox(height: 28),
              Row(
                children: [
                  const Icon(Icons.payments_outlined,
                      color: AppColors.onSurfaceVariant, size: 20),
                  const SizedBox(width: 8),
                  Text('Daily Food Budget',
                      style: AppTextStyles.headlineMd.copyWith(fontSize: 18)),
                ],
              ),
              const SizedBox(height: 8),
              Center(
                child: Text('\$${_budget.round()}',
                    style: AppTextStyles.displayLg
                        .copyWith(fontSize: 36, color: AppColors.primary)),
              ),
              SliderTheme(
                data: SliderTheme.of(context).copyWith(
                  activeTrackColor: AppColors.primary,
                  inactiveTrackColor: AppColors.surfaceContainerHigh,
                  thumbColor: AppColors.primary,
                  overlayColor: AppColors.primary.withOpacity(0.1),
                ),
                child: Slider(
                  value: _budget,
                  min: 15,
                  max: 150,
                  onChanged: (v) => setState(() => _budget = v),
                ),
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('\$15',
                      style: AppTextStyles.labelSm
                          .copyWith(color: AppColors.outline)),
                  Text('\$150+',
                      style: AppTextStyles.labelSm
                          .copyWith(color: AppColors.outline)),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                  'This helps us recommend meals and ingredients within your preferred spending range.',
                  style: AppTextStyles.labelMd
                      .copyWith(color: AppColors.onSurfaceVariant)),
              const SizedBox(height: 28),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () =>
                          Navigator.of(context).pushNamed('/plan-ready'),
                      style: OutlinedButton.styleFrom(
                          shape: RoundedRectangleBorder(
                              borderRadius:
                                  BorderRadius.circular(AppRadius.full))),
                      child: const Text('Skip'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      onPressed: () =>
                          Navigator.of(context).pushNamed('/plan-ready'),
                      style: ElevatedButton.styleFrom(
                          shape: RoundedRectangleBorder(
                              borderRadius:
                                  BorderRadius.circular(AppRadius.full))),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text('Complete Profile'),
                          SizedBox(width: 8),
                          Icon(Icons.check_circle, size: 18),
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
