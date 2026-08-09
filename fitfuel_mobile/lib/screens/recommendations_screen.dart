import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class _RecMeal {
  final int match;
  final String tag;
  final String name;
  final String price;
  final String restaurant;
  final String protein;
  final String carbs;
  final String fat;
  final String kcal;
  final String whyLabel;
  final String whyValue;
  const _RecMeal({
    required this.match,
    required this.tag,
    required this.name,
    required this.price,
    required this.restaurant,
    required this.protein,
    required this.carbs,
    required this.fat,
    required this.kcal,
    required this.whyLabel,
    required this.whyValue,
  });
}

class RecommendationsScreen extends StatefulWidget {
  const RecommendationsScreen({super.key});

  @override
  State<RecommendationsScreen> createState() => _RecommendationsScreenState();
}

class _RecommendationsScreenState extends State<RecommendationsScreen> {
  int _mealType = 0;
  final _tabs = const ['Breakfast', 'Lunch', 'Dinner', 'Snack'];

  final _meals = const [
    _RecMeal(
      match: 98,
      tag: 'High Protein',
      name: 'Protein Berry Oats',
      price: '₹249',
      restaurant: 'Healthy Kitchen',
      protein: '24g Pro',
      carbs: '45g Carbs',
      fat: '12g Fat',
      kcal: '380 kcal',
      whyLabel: 'Protein Target',
      whyValue: '+15%',
    ),
    _RecMeal(
      match: 92,
      tag: 'Low Carb',
      name: 'Spinach Egg White Omelette',
      price: '₹189',
      restaurant: 'Fit Bites',
      protein: '18g Pro',
      carbs: '5g Carbs',
      fat: '14g Fat',
      kcal: '220 kcal',
      whyLabel: 'Fat Burn Zone',
      whyValue: 'Optimal',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('FitFuel'),
        actions: [
          IconButton(
              icon: const Icon(Icons.notifications_outlined), onPressed: () {}),
        ],
      ),
      body: SafeArea(
        top: false,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.marginMobile, vertical: 12),
              child: PillTabSelector(
                tabs: _tabs,
                selectedIndex: _mealType,
                onChanged: (i) => setState(() => _mealType = i),
              ),
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.marginMobile, vertical: 8),
                children: [
                  Text('AI Recommendations for ${_tabs[_mealType]}',
                      style: AppTextStyles.headlineMd.copyWith(fontSize: 18)),
                  const SizedBox(height: 4),
                  Text('Based on your recent activity and macro goals.',
                      style: AppTextStyles.bodyMd
                          .copyWith(color: AppColors.onSurfaceVariant)),
                  const SizedBox(height: 16),
                  ..._meals.map((m) => Padding(
                        padding: const EdgeInsets.only(bottom: 16),
                        child: _MealRecCard(meal: m),
                      )),
                ],
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: FitFuelBottomNav(
        currentIndex: 1,
        onTap: (i) {
          if (i == 0) Navigator.of(context).pushReplacementNamed('/dashboard');
          if (i == 2) Navigator.of(context).pushNamed('/progress');
        },
      ),
    );
  }
}

class _MealRecCard extends StatefulWidget {
  final _RecMeal meal;
  const _MealRecCard({required this.meal});

  @override
  State<_MealRecCard> createState() => _MealRecCardState();
}

class _MealRecCardState extends State<_MealRecCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final m = widget.meal;
    return AppCard(
      radius: 20,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              MatchScoreChip(score: m.match),
              const Spacer(),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.primaryContainer.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(AppRadius.full),
                ),
                child: Text(m.tag,
                    style: AppTextStyles.labelSm
                        .copyWith(color: AppColors.primary)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(m.name,
                    style: AppTextStyles.headlineMd.copyWith(fontSize: 17)),
              ),
              Text(m.price,
                  style: AppTextStyles.headlineMd
                      .copyWith(fontSize: 17, color: AppColors.primary)),
            ],
          ),
          Text(m.restaurant,
              style: AppTextStyles.labelMd
                  .copyWith(color: AppColors.onSurfaceVariant)),
          const SizedBox(height: 12),
          Wrap(
            spacing: 16,
            runSpacing: 6,
            children: [
              _StatChip(icon: Icons.fitness_center, label: m.protein),
              _StatChip(icon: Icons.grass, label: m.carbs),
              _StatChip(icon: Icons.water_drop, label: m.fat),
              _StatChip(icon: Icons.local_fire_department, label: m.kcal),
            ],
          ),
          const SizedBox(height: 8),
          InkWell(
            onTap: () => setState(() => _expanded = !_expanded),
            child: Row(
              children: [
                Text('Why this meal?', style: AppTextStyles.labelMd),
                Icon(_expanded ? Icons.expand_less : Icons.expand_more,
                    size: 18, color: AppColors.onSurfaceVariant),
              ],
            ),
          ),
          if (_expanded)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.surfaceContainerLow,
                  borderRadius: BorderRadius.circular(AppRadius.dflt),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(m.whyLabel, style: AppTextStyles.labelMd),
                    Text(m.whyValue,
                        style: AppTextStyles.labelMd.copyWith(
                            color: AppColors.primary,
                            fontWeight: FontWeight.w700)),
                  ],
                ),
              ),
            ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: () {},
                  style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFFC8019)),
                  child: const Text('Order on Swiggy'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: OutlinedButton(
                  onPressed: () {},
                  style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFFE23744),
                      side: const BorderSide(color: Color(0xFFE23744))),
                  child: const Text('Order on Zomato'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            'Opens the platform\u2019s own search — complete checkout there.',
            style: AppTextStyles.labelSm.copyWith(color: AppColors.outline),
          ),
        ],
      ),
    );
  }
}

class _StatChip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _StatChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: AppColors.onSurfaceVariant),
        const SizedBox(width: 4),
        Text(label,
            style:
                AppTextStyles.labelSm.copyWith(color: AppColors.onSurfaceVariant)),
      ],
    );
  }
}
