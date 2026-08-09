import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Image.asset('assets/images/logo.png', width: 24, height: 24),
            const SizedBox(width: 8),
            const Text('FitFuel'),
          ],
        ),
        actions: [
          IconButton(
              icon: const Icon(Icons.notifications_outlined), onPressed: () {}),
        ],
      ),
      body: SafeArea(
        top: false,
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.marginMobile, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('Good morning, Alex.', style: AppTextStyles.headlineLgMobile),
              const SizedBox(height: 4),
              Text("You're on track. Let's conquer today.",
                  style: AppTextStyles.bodyMd
                      .copyWith(color: AppColors.onSurfaceVariant)),
              const SizedBox(height: 20),
              AppCard(
                radius: 20,
                padding: const EdgeInsets.all(20),
                child: Row(
                  children: [
                    Expanded(
                      flex: 3,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: const [
                          _MacroBar(label: 'Protein', current: 85, target: 150, color: AppColors.primary),
                          SizedBox(height: 14),
                          _MacroBar(label: 'Carbs', current: 120, target: 200, color: AppColors.secondaryContainer),
                          SizedBox(height: 14),
                          _MacroBar(label: 'Fat', current: 40, target: 65, color: AppColors.tertiaryContainer),
                        ],
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      flex: 2,
                      child: MacroRing(
                        progress: 0.65,
                        color: AppColors.primary,
                        size: 100,
                        center: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text('1.2k', style: AppTextStyles.headlineMd.copyWith(fontSize: 20)),
                            Text('Kcal Left', style: AppTextStyles.labelSm.copyWith(color: AppColors.onSurfaceVariant)),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              AppCard(
                radius: 20,
                child: Row(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.1),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.trending_down, color: AppColors.primary),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Weight Trend', style: AppTextStyles.bodyMd.copyWith(fontWeight: FontWeight.w600)),
                          Text('Past 7 days', style: AppTextStyles.labelSm.copyWith(color: AppColors.onSurfaceVariant)),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text('-0.8 lbs', style: AppTextStyles.bodyMd.copyWith(color: AppColors.primary, fontWeight: FontWeight.w700)),
                        Text('175.2 lbs current', style: AppTextStyles.labelSm.copyWith(color: AppColors.onSurfaceVariant)),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text("Today's Recommendations", style: AppTextStyles.headlineMd.copyWith(fontSize: 18)),
                  GestureDetector(
                    onTap: () => Navigator.of(context).pushNamed('/recommendations'),
                    child: Text('View All', style: AppTextStyles.labelMd.copyWith(color: AppColors.primary)),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              SizedBox(
                height: 190,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children: [
                    _MealCard(
                        match: 98,
                        title: 'Grilled Salmon & Quinoa',
                        meta: '450 kcal • 42g Protein',
                        onTap: () => Navigator.of(context).pushNamed('/meal-detail')),
                    _MealCard(
                        match: 92,
                        title: 'Green Power Smoothie',
                        meta: '320 kcal • 15g Protein',
                        onTap: () => Navigator.of(context).pushNamed('/meal-detail')),
                    _MealCard(
                        match: 88,
                        title: 'Harvest Grain Bowl',
                        meta: '510 kcal • 18g Protein',
                        onTap: () => Navigator.of(context).pushNamed('/meal-detail')),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              Row(
                children: [
                  Expanded(
                      child: _QuickAction(
                          icon: Icons.chat_bubble_outline,
                          title: 'Coach Chat',
                          subtitle: 'Ask questions')),
                  const SizedBox(width: 12),
                  Expanded(
                      child: _QuickAction(
                          icon: Icons.insert_chart_outlined,
                          title: 'Full Progress',
                          subtitle: 'Detailed stats',
                          onTap: () =>
                              Navigator.of(context).pushNamed('/progress'))),
                  const SizedBox(width: 12),
                  Expanded(
                      child: _QuickAction(
                          icon: Icons.menu_book_outlined,
                          title: 'Meal Plan',
                          subtitle: 'Edit schedule',
                          onTap: () =>
                              Navigator.of(context).pushNamed('/weekly-plan'))),
                ],
              ),
              const SizedBox(height: 12),
            ],
          ),
        ),
      ),
      bottomNavigationBar: FitFuelBottomNav(
        currentIndex: 0,
        onTap: (i) {
          if (i == 1) Navigator.of(context).pushNamed('/recommendations');
          if (i == 2) Navigator.of(context).pushNamed('/progress');
        },
      ),
    );
  }
}

class _MacroBar extends StatelessWidget {
  final String label;
  final double current;
  final double target;
  final Color color;
  const _MacroBar(
      {required this.label,
      required this.current,
      required this.target,
      required this.color});

  @override
  Widget build(BuildContext context) {
    final progress = (current / target).clamp(0, 1).toDouble();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: AppTextStyles.labelMd),
            Text('${current.round()}g / ${target.round()}g',
                style: AppTextStyles.labelSm
                    .copyWith(color: AppColors.onSurfaceVariant)),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.full),
          child: LinearProgressIndicator(
            value: progress,
            minHeight: 8,
            backgroundColor: AppColors.surfaceContainerHigh,
            color: color,
          ),
        ),
      ],
    );
  }
}

class _MealCard extends StatelessWidget {
  final int match;
  final String title;
  final String meta;
  final VoidCallback? onTap;
  const _MealCard(
      {required this.match,
      required this.title,
      required this.meta,
      this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 160,
        margin: const EdgeInsets.only(right: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          boxShadow: kCardShadowLevel1,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 90,
              decoration: BoxDecoration(
                borderRadius:
                    const BorderRadius.vertical(top: Radius.circular(16)),
                gradient: const LinearGradient(
                  colors: [AppColors.primaryContainer, AppColors.primary],
                ),
              ),
              child: Stack(
                children: [
                  const Center(
                      child: Icon(Icons.restaurant, color: Colors.white, size: 32)),
                  Positioned(top: 8, left: 8, child: MatchScoreChip(score: match)),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: AppTextStyles.bodyMd
                          .copyWith(fontWeight: FontWeight.w600, fontSize: 13)),
                  const SizedBox(height: 4),
                  Text(meta,
                      style: AppTextStyles.labelSm
                          .copyWith(color: AppColors.onSurfaceVariant)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _QuickAction extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback? onTap;
  const _QuickAction(
      {required this.icon,
      required this.title,
      required this.subtitle,
      this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AppCard(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 10),
        child: Column(
          children: [
            Icon(icon, color: AppColors.primary),
            const SizedBox(height: 8),
            Text(title,
                textAlign: TextAlign.center,
                style: AppTextStyles.labelMd
                    .copyWith(fontWeight: FontWeight.w700)),
            Text(subtitle,
                textAlign: TextAlign.center,
                style: AppTextStyles.labelSm
                    .copyWith(color: AppColors.onSurfaceVariant)),
          ],
        ),
      ),
    );
  }
}
