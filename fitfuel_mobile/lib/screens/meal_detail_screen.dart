import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class MealDetailScreen extends StatelessWidget {
  const MealDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Stack(
                children: [
                  Container(
                    height: 220,
                    decoration: const BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [
                          AppColors.primaryContainer,
                          AppColors.primary,
                        ],
                      ),
                    ),
                    child: const Center(
                      child:
                          Icon(Icons.set_meal, color: Colors.white, size: 64),
                    ),
                  ),
                  Positioned(
                    top: 12,
                    left: 12,
                    child: SafeArea(
                      child: GestureDetector(
                        onTap: () => Navigator.of(context).maybePop(),
                        child: Container(
                          padding: const EdgeInsets.all(8),
                          decoration: const BoxDecoration(
                            color: Colors.white,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.arrow_back, size: 20),
                        ),
                      ),
                    ),
                  ),
                  Positioned(
                    top: 16,
                    right: 16,
                    child: SafeArea(child: MatchScoreChip(score: 98)),
                  ),
                ],
              ),
              Padding(
                padding: const EdgeInsets.all(AppSpacing.marginMobile),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Wrap(
                      spacing: 8,
                      children: const [
                        _TagChip(label: 'High Protein'),
                        _TagChip(label: 'Pescatarian'),
                        _TagChip(label: 'Japanese Fusion'),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text('Miso Glazed Salmon Bowl',
                        style: AppTextStyles.headlineLgMobile),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        const Icon(Icons.restaurant,
                            size: 16, color: AppColors.onSurfaceVariant),
                        const SizedBox(width: 6),
                        Text('Green Leaf Eatery',
                            style: AppTextStyles.bodyMd
                                .copyWith(color: AppColors.onSurfaceVariant)),
                      ],
                    ),
                    const SizedBox(height: 20),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.primaryContainer.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(AppRadius.lg),
                        border: Border.all(
                            color: AppColors.primary.withOpacity(0.25)),
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
                                Text('Why FitFuel Recommends This',
                                    style: AppTextStyles.labelMd.copyWith(
                                        color: AppColors.primary,
                                        fontWeight: FontWeight.w700)),
                                const SizedBox(height: 4),
                                Text(
                                    'Perfectly aligns with your goal to increase omega-3 intake while staying under 600 calories. The quinoa base provides slow-release energy suitable for post-workout recovery.',
                                    style: AppTextStyles.labelMd.copyWith(
                                        color: AppColors.onSurfaceVariant)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),
                    Text('Macro Breakdown',
                        style: AppTextStyles.headlineMd.copyWith(fontSize: 18)),
                    const SizedBox(height: 12),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: const [
                        _MacroValue(value: '520', label: 'kcal'),
                        _MacroValue(value: '42g', label: 'Protein'),
                        _MacroValue(value: '38g', label: 'Carbs'),
                        _MacroValue(value: '22g', label: 'Fats'),
                      ],
                    ),
                    const SizedBox(height: 24),
                    Text('Allergens',
                        style: AppTextStyles.headlineMd.copyWith(fontSize: 18)),
                    const SizedBox(height: 12),
                    Row(
                      children: const [
                        _AllergenChip(icon: Icons.set_meal, label: 'Fish'),
                        SizedBox(width: 10),
                        _AllergenChip(icon: Icons.eco, label: 'Soy'),
                      ],
                    ),
                    const SizedBox(height: 28),
                    ElevatedButton(
                      onPressed: () {},
                      style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFFC8019)),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text('Order on Swiggy'),
                          SizedBox(width: 8),
                          Icon(Icons.arrow_forward, size: 18),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton(
                      onPressed: () {},
                      style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFFE23744),
                          side: const BorderSide(color: Color(0xFFE23744))),
                      child: const Text('Order on Zomato'),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Opens the platform\u2019s own search — complete checkout there.',
                      textAlign: TextAlign.center,
                      style: AppTextStyles.labelSm
                          .copyWith(color: AppColors.outline),
                    ),
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

class _TagChip extends StatelessWidget {
  final String label;
  const _TagChip({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLow,
        borderRadius: BorderRadius.circular(AppRadius.full),
      ),
      child: Text(label,
          style: AppTextStyles.labelSm
              .copyWith(color: AppColors.onSurfaceVariant)),
    );
  }
}

class _MacroValue extends StatelessWidget {
  final String value;
  final String label;
  const _MacroValue({required this.value, required this.label});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value, style: AppTextStyles.headlineMd.copyWith(fontSize: 20)),
        Text(label,
            style: AppTextStyles.labelSm
                .copyWith(color: AppColors.onSurfaceVariant)),
      ],
    );
  }
}

class _AllergenChip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _AllergenChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLow,
        borderRadius: BorderRadius.circular(AppRadius.dflt),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: AppColors.onSurfaceVariant),
          const SizedBox(width: 6),
          Text(label, style: AppTextStyles.labelMd),
        ],
      ),
    );
  }
}
