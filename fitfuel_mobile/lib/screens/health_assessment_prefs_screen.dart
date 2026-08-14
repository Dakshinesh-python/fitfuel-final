import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';
import '../services/api_service.dart';

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
  double _budget = 500;
  final TextEditingController _budgetController =
      TextEditingController(text: '500');
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _budgetController.addListener(() {
      final val = double.tryParse(_budgetController.text);
      if (val != null && val > 0 && val != _budget) {
        setState(() => _budget = val);
      }
    });
  }

  @override
  void dispose() {
    _budgetController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final args =
        ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>? ??
            {};

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final payload = {
        ...args,
        'dietaryPreference': _diet,
        'allergies': _allergies.toList(),
        'dailyBudget': _budget,
      };
      final data =
          await ApiService.instance.post('/api/health-profile', body: payload);

      if (!mounted) return;
      Navigator.of(context)
          .pushReplacementNamed('/plan-ready', arguments: data);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (e) {
      setState(() => _error = 'Something went wrong.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

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

  Future<void> _showAddAllergyDialog() async {
    String newAllergy = '';
    await showDialog(
        context: context,
        builder: (context) {
          return AlertDialog(
            title: const Text('Add Allergy/Restriction'),
            content: TextField(
              autofocus: true,
              decoration: const InputDecoration(
                hintText: 'e.g., Soy, Peanuts...',
              ),
              onChanged: (val) => newAllergy = val,
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () {
                  if (newAllergy.trim().isNotEmpty) {
                    setState(() {
                      _allergies.add(newAllergy.trim());
                    });
                  }
                  Navigator.pop(context);
                },
                child: const Text('Add'),
              ),
            ],
          );
        });
  }

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
                      padding: EdgeInsets.only(right: d == _diets.last ? 0 : 8),
                      child: GestureDetector(
                        onTap: () => setState(() => _diet = key),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 150),
                          padding: const EdgeInsets.symmetric(
                              vertical: 16, horizontal: 8),
                          decoration: BoxDecoration(
                            color: selected
                                ? AppColors.primaryContainer.withOpacity(0.12)
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
                children: [
                  ..._allergyOptions.map((a) {
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
                  }),
                  ..._allergies
                      .where((a) => !_allergyOptions.contains(a))
                      .map((a) {
                    return SelectableChip(
                      label: a,
                      selected: true,
                      onTap: () => setState(() => _allergies.remove(a)),
                    );
                  }),
                  GestureDetector(
                    onTap: _showAddAllergyDialog,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.transparent,
                        borderRadius: BorderRadius.circular(100),
                        border: Border.all(color: AppColors.outlineVariant),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.add,
                              size: 16, color: AppColors.onSurfaceVariant),
                          const SizedBox(width: 4),
                          Text('Add Other',
                              style: AppTextStyles.labelMd
                                  .copyWith(color: AppColors.onSurfaceVariant)),
                        ],
                      ),
                    ),
                  ),
                ],
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
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Text('₹',
                      style: AppTextStyles.displayLg
                          .copyWith(fontSize: 36, color: AppColors.primary)),
                  IntrinsicWidth(
                    child: TextField(
                      controller: _budgetController,
                      keyboardType: TextInputType.number,
                      textAlign: TextAlign.center,
                      style: AppTextStyles.displayLg
                          .copyWith(fontSize: 36, color: AppColors.primary),
                      decoration: const InputDecoration(
                        border: InputBorder.none,
                        isDense: true,
                        contentPadding: EdgeInsets.zero,
                      ),
                    ),
                  ),
                ],
              ),
              SliderTheme(
                data: SliderTheme.of(context).copyWith(
                  activeTrackColor: AppColors.primary,
                  inactiveTrackColor: AppColors.surfaceContainerHigh,
                  thumbColor: AppColors.primary,
                  overlayColor: AppColors.primary.withOpacity(0.1),
                ),
                child: Slider(
                  value: _budget.clamp(50.0, 1000.0),
                  min: 50,
                  max: 1000,
                  onChanged: (v) {
                    setState(() {
                      _budget = v;
                    });
                    // Avoid moving cursor to start when dragging
                    if (_budgetController.text != v.round().toString()) {
                      _budgetController.text = v.round().toString();
                    }
                  },
                ),
              ),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('₹50',
                      style: AppTextStyles.labelSm
                          .copyWith(color: AppColors.outline)),
                  Text('₹1000+',
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
              if (_error != null) ...[
                Text(_error!,
                    style:
                        AppTextStyles.labelMd.copyWith(color: AppColors.error)),
                const SizedBox(height: 16),
              ],
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _loading
                          ? null
                          : () {
                              // Skip could send default data or just push without API call,
                              // but here we just go to dashboard or plan-ready?
                              // Actually let's just push /plan-ready directly without data (will fail if no args handled gracefully)
                              Navigator.of(context).pushNamed('/plan-ready');
                            },
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
                      onPressed: _loading ? null : _submit,
                      style: ElevatedButton.styleFrom(
                          shape: RoundedRectangleBorder(
                              borderRadius:
                                  BorderRadius.circular(AppRadius.full))),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          if (_loading)
                            const SizedBox(
                                width: 16,
                                height: 16,
                                child: CircularProgressIndicator(
                                    color: Colors.white, strokeWidth: 2))
                          else ...[
                            const Text('Complete Profile'),
                            const SizedBox(width: 8),
                            const Icon(Icons.check_circle, size: 18),
                          ]
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
