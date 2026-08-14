import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../theme/app_theme.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Bottom Navigation Bar  (5 tabs: Home | Meals | Chat | Progress | Profile)
// ─────────────────────────────────────────────────────────────────────────────

class FitFuelBottomNav extends StatelessWidget {
  final int currentIndex; // -1 = none highlighted
  final ValueChanged<int> onTap;
  const FitFuelBottomNav(
      {super.key, required this.currentIndex, required this.onTap});

  static const _items = [
    (Icons.home_rounded, 'Home'),
    (Icons.restaurant_menu_rounded, 'Meals'),
    (Icons.chat_bubble_rounded, 'Chat'),
    (Icons.show_chart_rounded, 'Progress'),
    (Icons.person_rounded, 'Profile'),
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Color(0xFFEEF0EE), width: 1)),
        boxShadow: [
          BoxShadow(
              color: Color(0x0D000000), offset: Offset(0, -4), blurRadius: 16)
        ],
      ),
      child: SafeArea(
        top: false,
        child: SizedBox(
          height: 64,
          child: Row(
            children: List.generate(_items.length, (i) {
              final selected = i == currentIndex;
              final (icon, label) = _items[i];
              // The Chat tab (index 2) gets a special raised pill
              if (i == 2) {
                return Expanded(
                  child: GestureDetector(
                    onTap: () => onTap(i),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 44,
                          height: 30,
                          decoration: BoxDecoration(
                            gradient: const LinearGradient(
                              colors: [Color(0xFF2A9D58), Color(0xFF006C4D)],
                            ),
                            borderRadius: BorderRadius.circular(AppRadius.full),
                            boxShadow: [
                              BoxShadow(
                                  color:
                                      AppColors.primary.withValues(alpha: 0.3),
                                  offset: const Offset(0, 4),
                                  blurRadius: 10)
                            ],
                          ),
                          child: const Icon(Icons.chat_bubble_rounded,
                              color: Colors.white, size: 18),
                        ),
                        const SizedBox(height: 2),
                        Text(label,
                            style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                                color: selected
                                    ? AppColors.primary
                                    : AppColors.outline)),
                      ],
                    ),
                  ),
                );
              }
              return Expanded(
                child: GestureDetector(
                  onTap: () => onTap(i),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: selected
                                ? AppColors.primary.withValues(alpha: 0.1)
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(AppRadius.full),
                          ),
                          child: Icon(icon,
                              color: selected
                                  ? AppColors.primary
                                  : AppColors.outline,
                              size: 22),
                        ),
                        const SizedBox(height: 1),
                        Text(label,
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight:
                                  selected ? FontWeight.w700 : FontWeight.w500,
                              color: selected
                                  ? AppColors.primary
                                  : AppColors.outline,
                            )),
                      ],
                    ),
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

// ─────────────────────────────────────────────────────────────────────────────
// App Card  (white, elevated, rounded)
// ─────────────────────────────────────────────────────────────────────────────

class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;
  final Color? color;
  const AppCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(16),
    this.radius = AppRadius.lg,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: color ?? AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(radius),
        boxShadow: kCardShadowLevel1,
      ),
      child: child,
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Gradient Hero Card
// ─────────────────────────────────────────────────────────────────────────────

class GradientHeroCard extends StatelessWidget {
  final List<Color> colors;
  final Widget child;
  final double radius;
  const GradientHeroCard({
    super.key,
    required this.colors,
    required this.child,
    this.radius = AppRadius.xl,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
            colors: colors,
            begin: Alignment.topLeft,
            end: Alignment.bottomRight),
        borderRadius: BorderRadius.circular(radius),
        boxShadow: [
          BoxShadow(
              color: colors.first.withValues(alpha: 0.35),
              offset: const Offset(0, 8),
              blurRadius: 20)
        ],
      ),
      child: child,
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Pill Tab Selector
// ─────────────────────────────────────────────────────────────────────────────

class PillTabSelector extends StatelessWidget {
  final List<String> tabs;
  final int selectedIndex;
  final ValueChanged<int> onChanged;
  const PillTabSelector({
    super.key,
    required this.tabs,
    required this.selectedIndex,
    required this.onChanged,
  });

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
                padding: const EdgeInsets.symmetric(vertical: 9),
                decoration: BoxDecoration(
                  gradient: selected
                      ? const LinearGradient(
                          colors: [Color(0xFF2A9D58), Color(0xFF006C4D)])
                      : null,
                  color: selected ? null : Colors.transparent,
                  borderRadius: BorderRadius.circular(AppRadius.full),
                  boxShadow: selected ? kCardShadowLevel1 : null,
                ),
                alignment: Alignment.center,
                child: Text(
                  tabs[i],
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                    color: selected ? Colors.white : AppColors.onSurfaceVariant,
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

// ─────────────────────────────────────────────────────────────────────────────
// Macro progress bar row
// ─────────────────────────────────────────────────────────────────────────────

class MacroProgressRow extends StatelessWidget {
  final String label;
  final int current;
  final int target;
  final Color color;
  const MacroProgressRow({
    super.key,
    required this.label,
    required this.current,
    required this.target,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final pct = target > 0 ? (current / target).clamp(0.0, 1.0) : 0.0;
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label,
                  style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFF374151))),
              Text('${target}g',
                  style: TextStyle(
                      fontSize: 12, fontWeight: FontWeight.w700, color: color)),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(AppRadius.full),
            child: LinearProgressIndicator(
              value: pct,
              backgroundColor: color.withValues(alpha: 0.12),
              valueColor: AlwaysStoppedAnimation(color),
              minHeight: 8,
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Stat chip (small colored badge)
// ─────────────────────────────────────────────────────────────────────────────

class StatChip extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  final IconData icon;
  const StatChip({
    super.key,
    required this.label,
    required this.value,
    required this.color,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(AppRadius.md),
          border: Border.all(color: color.withValues(alpha: 0.15)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 18),
            const SizedBox(height: 8),
            Text(value,
                style: TextStyle(
                    fontSize: 16, fontWeight: FontWeight.w800, color: color)),
            const SizedBox(height: 2),
            Text(label,
                style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                    color: Color(0xFF6B7280))),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// MacroRing (unchanged — keep for backward compat)
// ─────────────────────────────────────────────────────────────────────────────

class MacroRing extends StatelessWidget {
  final double progress;
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

// ─────────────────────────────────────────────────────────────────────────────
// StepProgressBar, SelectableOptionCard, SelectableChip, MatchScoreChip
// (unchanged — keep for health assessment screens)
// ─────────────────────────────────────────────────────────────────────────────

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
              color:
                  active ? AppColors.primary : AppColors.surfaceContainerHigh,
              borderRadius: BorderRadius.circular(AppRadius.full),
            ),
          ),
        );
      }),
    );
  }
}

class MatchScoreChip extends StatelessWidget {
  final int score;
  const MatchScoreChip({super.key, required this.score});

  Color get _color {
    if (score >= 95) return const Color(0xFF2A9D58);
    if (score >= 80) return const Color(0xFFF59E0B);
    return const Color(0xFFEF4444);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: _color,
        borderRadius: BorderRadius.circular(AppRadius.full),
      ),
      child: Text('$score% Match',
          style: const TextStyle(
              color: Colors.white, fontSize: 11, fontWeight: FontWeight.w700)),
    );
  }
}

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
              ? AppColors.primaryContainer.withValues(alpha: 0.12)
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
              const Icon(Icons.check_circle,
                  color: AppColors.primary, size: 22),
          ],
        ),
      ),
    );
  }
}

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

// Shared AppBar widget
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
