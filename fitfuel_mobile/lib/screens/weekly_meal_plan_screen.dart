import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class _PlanMeal {
  final String slot;
  final int match;
  final String name;
  final String desc;
  final String cals;
  final String protein;
  const _PlanMeal(
      {required this.slot,
      required this.match,
      required this.name,
      required this.desc,
      required this.cals,
      required this.protein});
}

class WeeklyMealPlanScreen extends StatefulWidget {
  const WeeklyMealPlanScreen({super.key});

  @override
  State<WeeklyMealPlanScreen> createState() => _WeeklyMealPlanScreenState();
}

class _WeeklyMealPlanScreenState extends State<WeeklyMealPlanScreen> {
  int _selectedDay = 1;
  final _days = const [
    ('Mon', 12),
    ('Tue', 13),
    ('Wed', 14),
    ('Thu', 15),
    ('Fri', 16),
    ('Sat', 17),
    ('Sun', 18),
  ];

  final _meals = const [
    _PlanMeal(
        slot: 'Breakfast',
        match: 98,
        name: 'Berry Protein Bowl',
        desc: 'Greek yogurt, mixed berries, chia seeds.',
        cals: '420',
        protein: '28g'),
    _PlanMeal(
        slot: 'Lunch',
        match: 95,
        name: 'Quinoa Chicken Salad',
        desc: 'Grilled breast, avocado, lemon vinaigrette.',
        cals: '650',
        protein: '45g'),
    _PlanMeal(
        slot: 'Snack',
        match: 88,
        name: 'Almonds & Apple',
        desc: 'Raw almonds with crisp green apple slices.',
        cals: '220',
        protein: '6g'),
    _PlanMeal(
        slot: 'Dinner',
        match: 99,
        name: 'Miso Glazed Salmon',
        desc: 'Wild caught salmon, asparagus, wild rice.',
        cals: '710',
        protein: '52g'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Meal Plan'),
        actions: [
          IconButton(
              icon: const Icon(Icons.notifications_outlined), onPressed: () {}),
        ],
      ),
      body: SafeArea(
        top: false,
        child: ListView(
          padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.marginMobile, vertical: 16),
          children: [
            Text('Weekly Plan', style: AppTextStyles.headlineLgMobile),
            const SizedBox(height: 4),
            Text('Your personalized AI-matched nutrition for the week.',
                style: AppTextStyles.bodyMd
                    .copyWith(color: AppColors.onSurfaceVariant)),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.08),
                borderRadius: BorderRadius.circular(AppRadius.full),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.bolt, size: 16, color: AppColors.primary),
                  const SizedBox(width: 4),
                  Text('2,450 kcal / day',
                      style: AppTextStyles.labelMd
                          .copyWith(color: AppColors.primary)),
                ],
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              height: 68,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: _days.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (context, i) {
                  final (label, date) = _days[i];
                  final selected = i == _selectedDay;
                  return GestureDetector(
                    onTap: () => setState(() => _selectedDay = i),
                    child: Container(
                      width: 52,
                      decoration: BoxDecoration(
                        color: selected ? AppColors.primary : Colors.white,
                        borderRadius: BorderRadius.circular(AppRadius.md),
                        boxShadow: kCardShadowLevel1,
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(label,
                              style: AppTextStyles.labelSm.copyWith(
                                  color: selected
                                      ? Colors.white
                                      : AppColors.onSurfaceVariant)),
                          const SizedBox(height: 4),
                          Text('$date',
                              style: AppTextStyles.bodyMd.copyWith(
                                  fontWeight: FontWeight.w700,
                                  color: selected
                                      ? Colors.white
                                      : AppColors.onSurface)),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 20),
            ..._meals.map((m) => Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: AppCard(
                    radius: 18,
                    child: Row(
                      children: [
                        Container(
                          width: 56,
                          height: 56,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [
                                AppColors.primaryContainer,
                                AppColors.primary
                              ],
                            ),
                            borderRadius: BorderRadius.circular(AppRadius.dflt),
                          ),
                          child:
                              const Icon(Icons.restaurant, color: Colors.white),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Text(m.slot,
                                      style: AppTextStyles.labelSm.copyWith(
                                          color: AppColors.onSurfaceVariant)),
                                  const Spacer(),
                                  Text('${m.match}%',
                                      style: AppTextStyles.labelSm.copyWith(
                                          color: AppColors.primary,
                                          fontWeight: FontWeight.w700)),
                                ],
                              ),
                              Text(m.name,
                                  style: AppTextStyles.bodyMd
                                      .copyWith(fontWeight: FontWeight.w700)),
                              Text(m.desc,
                                  style: AppTextStyles.labelSm.copyWith(
                                      color: AppColors.onSurfaceVariant)),
                              const SizedBox(height: 4),
                              Text('Cals ${m.cals} · Pro ${m.protein}',
                                  style: AppTextStyles.labelSm.copyWith(
                                      color: AppColors.onSurfaceVariant)),
                            ],
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.swap_horiz,
                              color: AppColors.outline),
                          onPressed: () {},
                        ),
                      ],
                    ),
                  ),
                )),
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: () {},
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.auto_awesome, size: 18),
                  SizedBox(width: 8),
                  Text('Regenerate Plan'),
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
