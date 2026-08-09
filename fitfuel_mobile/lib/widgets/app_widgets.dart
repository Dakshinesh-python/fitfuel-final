import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../theme/app_theme.dart';

/// Simple top app bar with back button + title, matching the glass nav style.
class FitFuelAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final List<Widget>? actions;
  final bool showBack;
  const FitFuelAppBar(
      {super.key, required this.title, this.actions, this.showBack = true});

  @override
  Widget build(BuildContext context) {
    return AppBar(
      title: Text(title),
      leading: showBack
          ? IconButton(
              icon: const Icon(Icons.arrow_back_ios_new, size: 20),
              onPressed: () => Navigator.of(context).maybePop(),
            )
          : null,
      actions: actions,
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}

/// Bottom navigation bar shared by dashboard / recommendations / progress etc.
class FitFuelBottomNav extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;
  const FitFuelBottomNav(
      {super.key, required this.currentIndex, required this.onTap});

  @override
  Widget build(BuildContext context) {
    const items = [
      (Icons.home_rounded, 'Home'),
      (Icons.restaurant_menu_rounded, 'Meals'),
      (Icons.show_chart_rounded, 'Progress'),
      (Icons.person_rounded, 'Profile'),
    ];
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.9),
        boxShadow: kCardShadowLevel1,
        border: const Border(
            top: BorderSide(color: AppColors.surfaceContainerHigh)),
      ),
      child: SafeArea(
        child: SizedBox(
          height: 64,
          child: Row(
            children: List.generate(items.length, (i) {
              final selected = i == currentIndex;
              final (icon, label) = items[i];
              return Expanded(
                child: InkWell(
                  onTap: () => onTap(i),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(icon,
                          color: selected
                              ? AppColors.primary
                              : AppColors.outline,
                          size: 24),
                      const SizedBox(height: 2),
                      Text(label,
                          style: AppTextStyles.labelSm.copyWith(
                              color: selected
                                  ? AppColors.primary
                                  : AppColors.outline)),
                    ],
                  ),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }
}

/// Pill-shaped "Match Score" chip using the coral gradient.
class MatchScoreChip extends StatelessWidget {
  final int score;
  const MatchScoreChip({super.key, required this.score});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.coralStart, AppColors.coralEnd],
        ),
        borderRadius: BorderRadius.circular(AppRadius.full),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.auto_awesome, size: 12, color: Colors.white),
          const SizedBox(width: 4),
          Text('$score% Match',
              style: AppTextStyles.labelSm.copyWith(color: Colors.white)),
        ],
      ),
    );
  }
}

/// A pill tab selector (segmented control) matching the "sliding blob" style.
class PillTabSelector extends StatelessWidget {
  final List<String> tabs;
  final int selectedIndex;
  final ValueChanged<int> onChanged;
  const PillTabSelector(
      {super.key,
      required this.tabs,
      required this.selectedIndex,
      required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: const Color(0xFFF3F4F6),
        borderRadius: BorderRadius.circular(AppRadius.full),
      ),
      child: Row(
        children: List.generate(tabs.length, (i) {
          final selected = i == selectedIndex;
          return Expanded(
            child: GestureDetector(
              onTap: () => onChanged(i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: selected ? Colors.white : Colors.transparent,
                  borderRadius: BorderRadius.circular(AppRadius.full),
                  boxShadow: selected ? kCardShadowLevel1 : null,
                ),
                alignment: Alignment.center,
                child: Text(
                  tabs[i],
                  style: AppTextStyles.labelMd.copyWith(
                    color: selected
                        ? AppColors.onSurface
                        : AppColors.onSurfaceVariant,
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                  ),
                ),
              ),
            ),
          );
        }),
      ),
    );
  }
}

/// A generic elevated white "card" surface with the design system's soft shadow.
class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;
  const AppCard(
      {super.key,
      required this.child,
      this.padding = const EdgeInsets.all(16),
      this.radius = AppRadius.lg});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(radius),
        boxShadow: kCardShadowLevel1,
      ),
      child: child,
    );
  }
}

/// A round macro-progress ring (e.g. protein/carbs/fat), thick stroke + rounded caps.
class MacroRing extends StatelessWidget {
  final double progress; // 0..1
  final Color color;
  final double size;
  final Widget? center;
  const MacroRing({
    super.key,
    required this.progress,
    required this.color,
    this.size = 72,
    this.center,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CustomPaint(
            size: Size(size, size),
            painter: _RingPainter(
                progress: progress,
                color: color,
                track: AppColors.surfaceContainerHigh),
          ),
          if (center != null) center!,
        ],
      ),
    );
  }
}

class _RingPainter extends CustomPainter {
  final double progress;
  final Color color;
  final Color track;
  _RingPainter(
      {required this.progress, required this.color, required this.track});

  @override
  void paint(Canvas canvas, Size size) {
    final stroke = size.width * 0.11;
    final rect = Rect.fromLTWH(
        stroke / 2, stroke / 2, size.width - stroke, size.height - stroke);
    final trackPaint = Paint()
      ..color = track
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke;
    final fgPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.round;
    canvas.drawArc(rect, 0, 2 * math.pi, false, trackPaint);
    canvas.drawArc(
        rect, -math.pi / 2, 2 * math.pi * progress.clamp(0, 1), false, fgPaint);
  }

  @override
  bool shouldRepaint(covariant _RingPainter oldDelegate) =>
      oldDelegate.progress != progress || oldDelegate.color != color;
}

/// A step progress indicator (used across onboarding & health assessment flow).
class StepProgressBar extends StatelessWidget {
  final int currentStep;
  final int totalSteps;
  const StepProgressBar(
      {super.key, required this.currentStep, required this.totalSteps});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(totalSteps, (i) {
        final active = i < currentStep;
        return Expanded(
          child: Container(
            margin: EdgeInsets.only(right: i == totalSteps - 1 ? 0 : 6),
            height: 6,
            decoration: BoxDecoration(
              color: active
                  ? AppColors.primary
                  : AppColors.surfaceContainerHigh,
              borderRadius: BorderRadius.circular(AppRadius.full),
            ),
          ),
        );
      }),
    );
  }
}

/// Selectable option card (used in health assessment goal/activity pickers).
class SelectableOptionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;
  final bool selected;
  final VoidCallback onTap;
  const SelectableOptionCard({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: selected
              ? AppColors.primaryContainer.withOpacity(0.12)
              : AppColors.surfaceContainerLowest,
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(
            color: selected ? AppColors.primary : AppColors.outlineVariant,
            width: selected ? 1.5 : 1,
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: selected
                    ? AppColors.primary
                    : AppColors.surfaceContainerHigh,
                borderRadius: BorderRadius.circular(AppRadius.dflt),
              ),
              child: Icon(icon,
                  color: selected ? Colors.white : AppColors.onSurfaceVariant,
                  size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: AppTextStyles.bodyMd.copyWith(
                          fontWeight: FontWeight.w600,
                          color: AppColors.onSurface)),
                  if (subtitle != null)
                    Text(subtitle!,
                        style: AppTextStyles.labelMd
                            .copyWith(color: AppColors.onSurfaceVariant)),
                ],
              ),
            ),
            if (selected)
              const Icon(Icons.check_circle, color: AppColors.primary, size: 22),
          ],
        ),
      ),
    );
  }
}

/// Pill chip used for allergies / dietary preference selectors.
class SelectableChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const SelectableChip(
      {super.key,
      required this.label,
      required this.selected,
      required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(
          color: selected ? AppColors.primary : AppColors.surfaceContainerLow,
          borderRadius: BorderRadius.circular(AppRadius.full),
          border: Border.all(
            color: selected ? AppColors.primary : AppColors.outlineVariant,
          ),
        ),
        child: Text(
          label,
          style: AppTextStyles.labelMd.copyWith(
            color: selected ? Colors.white : AppColors.onSurfaceVariant,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}
