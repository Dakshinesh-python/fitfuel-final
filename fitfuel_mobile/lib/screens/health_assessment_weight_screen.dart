import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class HealthAssessmentWeightScreen extends StatefulWidget {
  const HealthAssessmentWeightScreen({super.key});

  @override
  State<HealthAssessmentWeightScreen> createState() =>
      _HealthAssessmentWeightScreenState();
}

class _HealthAssessmentWeightScreenState
    extends State<HealthAssessmentWeightScreen> {
  final _targetWeightController = TextEditingController(text: '70');
  TextEditingController? _currentWeightController;
  bool _initialized = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_initialized) {
      final args =
          ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>? ??
              {};
      final initialWeight =
          (args['currentWeightKg'] as num?)?.toDouble() ?? 65.0;
      _currentWeightController =
          TextEditingController(text: initialWeight.toStringAsFixed(0));
      _initialized = true;
    }
  }

  double get _currentWeight {
    return double.tryParse(_currentWeightController?.text ?? '65') ?? 65.0;
  }

  double get _diff {
    final target = double.tryParse(_targetWeightController.text) ?? 0;
    return _currentWeight - target;
  }

  @override
  void dispose() {
    _currentWeightController?.dispose();
    _targetWeightController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final diff = _diff;
    final losing = diff >= 0;
    return Scaffold(
      appBar: const FitFuelAppBar(title: 'FitFuel', showBack: false),
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
                  Text('Step 1 of 4',
                      style: AppTextStyles.labelMd
                          .copyWith(color: AppColors.onSurfaceVariant)),
                  Text('Goals',
                      style: AppTextStyles.labelMd.copyWith(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w700)),
                ],
              ),
              const SizedBox(height: 8),
              const StepProgressBar(currentStep: 1, totalSteps: 4),
              const SizedBox(height: 32),
              Text("Let's set your baseline.",
                  textAlign: TextAlign.center,
                  style: AppTextStyles.headlineLgMobile),
              const SizedBox(height: 8),
              Text('Tell us where you are and where you want to be.',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.bodyMd
                      .copyWith(color: AppColors.onSurfaceVariant)),
              const SizedBox(height: 32),
              _WeightInputCard(
                fieldKey: const ValueKey('health_current_weight_field'),
                label: 'Current Weight (kg)',
                controller: _currentWeightController!,
                icon: Icons.monitor_weight_outlined,
                accent: AppColors.onSurface,
                iconColor: AppColors.outline,
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 16),
              _WeightInputCard(
                fieldKey: const ValueKey('health_target_weight_field'),
                label: 'Target Weight (kg)',
                controller: _targetWeightController,
                icon: Icons.flag_outlined,
                accent: AppColors.primary,
                iconColor: AppColors.primary,
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.surfaceContainerLow,
                  borderRadius: BorderRadius.circular(AppRadius.md),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Icon(losing ? Icons.trending_down : Icons.trending_up,
                            color: AppColors.secondaryContainer),
                        const SizedBox(width: 8),
                        Text('Goal: ${losing ? 'Lose' : 'Gain'}',
                            style: AppTextStyles.bodyMd
                                .copyWith(color: AppColors.onSurfaceVariant)),
                      ],
                    ),
                    Text('${diff.abs().toStringAsFixed(0)} kg',
                        style: AppTextStyles.headlineMd),
                  ],
                ),
              ),
              const SizedBox(height: 40),
              ElevatedButton(
                key: const ValueKey('health_weight_continue_button'),
                onPressed: () {
                  final targetKg =
                      double.tryParse(_targetWeightController.text) ?? 0;
                  Navigator.of(context).pushNamed(
                    '/health-activity',
                    arguments: {
                      'currentWeightKg': _currentWeight,
                      'targetWeightKg': targetKg,
                    },
                  );
                },
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

class _WeightInputCard extends StatelessWidget {
  final Key? fieldKey;
  final String label;
  final TextEditingController controller;
  final IconData icon;
  final Color accent;
  final Color iconColor;
  final ValueChanged<String> onChanged;
  const _WeightInputCard({
    this.fieldKey,
    required this.label,
    required this.controller,
    required this.icon,
    required this.accent,
    required this.iconColor,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      padding: const EdgeInsets.all(20),
      radius: 20,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: AppTextStyles.labelMd
                  .copyWith(color: AppColors.onSurfaceVariant)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: TextField(
                  key: fieldKey,
                  controller: controller,
                  onChanged: onChanged,
                  keyboardType: TextInputType.number,
                  style: AppTextStyles.displayLg
                      .copyWith(fontSize: 40, color: accent),
                  decoration: const InputDecoration(
                    border: InputBorder.none,
                    filled: false,
                    contentPadding: EdgeInsets.zero,
                    isDense: true,
                  ),
                ),
              ),
              Icon(icon, color: iconColor, size: 36),
            ],
          ),
        ],
      ),
    );
  }
}
