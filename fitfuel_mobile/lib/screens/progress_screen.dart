import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class ProgressScreen extends StatefulWidget {
  const ProgressScreen({super.key});

  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  int _range = 0; // 1M, 3M, YTD

  final _weightSpots = const [
    FlSpot(0, 168),
    FlSpot(1, 167.4),
    FlSpot(2, 167.8),
    FlSpot(3, 166.9),
    FlSpot(4, 165.9),
    FlSpot(5, 165.2),
    FlSpot(6, 164.5),
  ];

  void _openLogSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (context) => const _LogEntrySheet(),
    );
  }

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
        child: ListView(
          padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.marginMobile, vertical: 16),
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Your Progress', style: AppTextStyles.headlineLgMobile),
                      Text('Tracking your journey to better health.',
                          style: AppTextStyles.bodyMd
                              .copyWith(color: AppColors.onSurfaceVariant)),
                    ],
                  ),
                ),
                ElevatedButton(
                  onPressed: _openLogSheet,
                  style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 12),
                      minimumSize: Size.zero),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.add, size: 18),
                      SizedBox(width: 4),
                      Text('Log Entry'),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            AppCard(
              radius: 20,
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Weekly Goal Achievement',
                            style: AppTextStyles.labelMd.copyWith(
                                color: AppColors.onSurfaceVariant)),
                        const SizedBox(height: 8),
                        Text('82%', style: AppTextStyles.displayLg.copyWith(fontSize: 34)),
                        const SizedBox(height: 6),
                        Text(
                            'You are on track to meet your macro targets this week.',
                            style: AppTextStyles.labelMd.copyWith(
                                color: AppColors.onSurfaceVariant)),
                      ],
                    ),
                  ),
                  MacroRing(
                    progress: 0.82,
                    color: AppColors.primary,
                    size: 84,
                    center: const Icon(Icons.emoji_events,
                        color: AppColors.primary, size: 26),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: const [
                Expanded(
                    child: _MiniMacroCard(
                        label: 'Protein', value: 95, color: AppColors.primary)),
                SizedBox(width: 10),
                Expanded(
                    child: _MiniMacroCard(
                        label: 'Carbs',
                        value: 78,
                        color: AppColors.secondaryContainer)),
                SizedBox(width: 10),
                Expanded(
                    child: _MiniMacroCard(
                        label: 'Fats',
                        value: 85,
                        color: AppColors.tertiaryContainer)),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Weight Trend', style: AppTextStyles.headlineMd.copyWith(fontSize: 18)),
                PillTabSelector(
                  tabs: const ['1M', '3M', 'YTD'],
                  selectedIndex: _range,
                  onChanged: (i) => setState(() => _range = i),
                ),
              ],
            ),
            const SizedBox(height: 16),
            AppCard(
              radius: 20,
              child: SizedBox(
                height: 180,
                child: LineChart(
                  LineChartData(
                    gridData: const FlGridData(show: false),
                    titlesData: const FlTitlesData(show: false),
                    borderData: FlBorderData(show: false),
                    lineTouchData: const LineTouchData(enabled: true),
                    lineBarsData: [
                      LineChartBarData(
                        spots: _weightSpots,
                        isCurved: true,
                        color: AppColors.primary,
                        barWidth: 3,
                        dotData: const FlDotData(show: false),
                        belowBarData: BarAreaData(
                          show: true,
                          color: AppColors.primary.withOpacity(0.1),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Recent Logs', style: AppTextStyles.headlineMd.copyWith(fontSize: 18)),
                Text('View All', style: AppTextStyles.labelMd.copyWith(color: AppColors.primary)),
              ],
            ),
            const SizedBox(height: 12),
            const _LogRow(
                icon: Icons.monitor_weight_outlined,
                title: '164.5 lbs',
                subtitle: 'Today, 8:00 AM',
                trailingIcon: Icons.trending_down,
                trailingColor: AppColors.primary),
            const _LogRow(
                icon: Icons.restaurant_outlined,
                title: 'Macros Logged',
                subtitle: 'Yesterday, 7:30 PM',
                trailingIcon: Icons.check_circle,
                trailingColor: AppColors.primary),
            const _LogRow(
                icon: Icons.monitor_weight_outlined,
                title: '165.2 lbs',
                subtitle: 'Oct 12, 8:15 AM',
                trailingIcon: Icons.trending_up,
                trailingColor: AppColors.secondary),
            const _LogRow(
                icon: Icons.edit_note_outlined,
                title: 'Note Added',
                subtitle: 'Oct 10, 9:00 PM',
                trailingIcon: Icons.chevron_right,
                trailingColor: AppColors.outline),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _openLogSheet,
        backgroundColor: AppColors.primary,
        child: const Icon(Icons.add, color: Colors.white),
      ),
      bottomNavigationBar: FitFuelBottomNav(
        currentIndex: 2,
        onTap: (i) {
          if (i == 0) Navigator.of(context).pushReplacementNamed('/dashboard');
          if (i == 1) Navigator.of(context).pushNamed('/recommendations');
        },
      ),
    );
  }
}

class _MiniMacroCard extends StatelessWidget {
  final String label;
  final int value;
  final Color color;
  const _MiniMacroCard(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return AppCard(
      radius: 16,
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
      child: Column(
        children: [
          Text(label, style: AppTextStyles.labelSm.copyWith(color: AppColors.onSurfaceVariant)),
          const SizedBox(height: 6),
          Text('$value%', style: AppTextStyles.headlineMd.copyWith(fontSize: 18, color: color)),
        ],
      ),
    );
  }
}

class _LogRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final IconData trailingIcon;
  final Color trailingColor;
  const _LogRow({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.trailingIcon,
    required this.trailingColor,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: AppCard(
        radius: 14,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: AppColors.surfaceContainerLow,
                shape: BoxShape.circle,
              ),
              child: Icon(icon, size: 18, color: AppColors.onSurfaceVariant),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: AppTextStyles.bodyMd.copyWith(fontWeight: FontWeight.w600)),
                  Text(subtitle, style: AppTextStyles.labelSm.copyWith(color: AppColors.onSurfaceVariant)),
                ],
              ),
            ),
            Icon(trailingIcon, color: trailingColor, size: 20),
          ],
        ),
      ),
    );
  }
}

class _LogEntrySheet extends StatefulWidget {
  const _LogEntrySheet();

  @override
  State<_LogEntrySheet> createState() => _LogEntrySheetState();
}

class _LogEntrySheetState extends State<_LogEntrySheet> {
  final _weightController = TextEditingController();
  final _proteinController = TextEditingController();
  final _carbsController = TextEditingController();
  final _fatsController = TextEditingController();
  final _notesController = TextEditingController();

  @override
  void dispose() {
    _weightController.dispose();
    _proteinController.dispose();
    _carbsController.dispose();
    _fatsController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: AppSpacing.marginMobile,
        right: AppSpacing.marginMobile,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('New Log Entry', style: AppTextStyles.headlineMd.copyWith(fontSize: 18)),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text('Weight (lbs)', style: AppTextStyles.labelMd),
            const SizedBox(height: 6),
            TextField(
              controller: _weightController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.monitor_weight_outlined)),
            ),
            const SizedBox(height: 16),
            Text('Daily Macros (g)', style: AppTextStyles.labelMd),
            const SizedBox(height: 6),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _proteinController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(hintText: 'Protein'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _carbsController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(hintText: 'Carbs'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: TextField(
                    controller: _fatsController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(hintText: 'Fats'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text('Notes', style: AppTextStyles.labelMd),
            const SizedBox(height: 6),
            TextField(
              controller: _notesController,
              maxLines: 3,
              decoration: const InputDecoration(hintText: 'Optional notes...'),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.check, size: 18),
                  SizedBox(width: 8),
                  Text('Save Entry'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
