import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class ProgressScreen extends StatefulWidget {
  const ProgressScreen({super.key});

  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  // ── Data state ─────────────────────────────────────────────────────────────
  ProgressSummary? _summary;
  List<ProgressLog> _logs = [];
  List<WeightHistoryEntry> _weightHistory = [];
  bool _loading = true;
  String? _loadError;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _loadError = null;
    });
    try {
      // Three parallel API calls:
      //   GET /api/progress/summary    → { logs, weeklyAverageCalories, goalAchievementPct }
      //   GET /api/progress            → { logs: [...all entries] }
      //   GET /api/progress/weight-history → { weightHistory: [{date, weightKg}] }
      final results = await Future.wait([
        ApiService.instance.get('/api/progress/summary'),
        ApiService.instance.get('/api/progress'),
        ApiService.instance.get('/api/progress/weight-history'),
      ]);

      if (!mounted) return;
      setState(() {
        _summary = ProgressSummary.fromJson(results[0] as Map<String, dynamic>);
        _logs = (results[1]['logs'] as List)
            .map((e) => ProgressLog.fromJson(e as Map<String, dynamic>))
            .toList();
        _weightHistory = (results[2]['weightHistory'] as List)
            .map((e) => WeightHistoryEntry.fromJson(e as Map<String, dynamic>))
            .toList();
      });
    } on ApiException catch (e) {
      if (mounted) setState(() => _loadError = e.message);
    } catch (_) {
      if (mounted) {
        setState(() =>
            _loadError = 'Unable to load progress data. Please try again.');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _openLogSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (ctx) => _LogEntrySheet(onSubmitted: () {
        Navigator.of(ctx).pop();
        _loadData(); // refresh after log
      }),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: false,
        automaticallyImplyLeading: false,
        title: const Text('Progress',
            style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                color: Color(0xFF111827))),
      ),
      body: SafeArea(
        top: false,
        child: _buildBody(),
      ),
      bottomNavigationBar: FitFuelBottomNav(
        currentIndex: 3,
        onTap: (i) {
          if (i == 0) Navigator.of(context).pushReplacementNamed('/dashboard');
          if (i == 1)
            Navigator.of(context).pushReplacementNamed('/recommendations');
          if (i == 2) Navigator.of(context).pushNamed('/chat');
          if (i == 4) Navigator.of(context).pushReplacementNamed('/profile');
        },
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());

    if (_loadError != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.wifi_off_rounded,
                  size: 48, color: AppColors.outline),
              const SizedBox(height: 16),
              Text(_loadError!,
                  textAlign: TextAlign.center,
                  style: AppTextStyles.bodyMd
                      .copyWith(color: AppColors.onSurfaceVariant)),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                key: const ValueKey('progress_retry_button'),
                onPressed: _loadData,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.marginMobile, vertical: 16),
      children: [
        // Hero banner
        Container(
          margin: const EdgeInsets.only(bottom: 20),
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF3B82F6), Color(0xFF1D4ED8)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF3B82F6).withValues(alpha: 0.3),
                offset: const Offset(0, 6),
                blurRadius: 16,
              ),
            ],
          ),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Track your journey',
                        style: TextStyle(
                            color: Colors.white70,
                            fontSize: 12,
                            fontWeight: FontWeight.w500)),
                    const SizedBox(height: 4),
                    const Text('Your Progress',
                        style: TextStyle(
                            color: Colors.white,
                            fontSize: 22,
                            fontWeight: FontWeight.w800)),
                    const SizedBox(height: 4),
                    const Text('Weight trends & nutrition logs',
                        style: TextStyle(color: Colors.white60, fontSize: 11)),
                  ],
                ),
              ),
              ElevatedButton.icon(
                key: const ValueKey('progress_log_button'),
                onPressed: _openLogSheet,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: const Color(0xFF1D4ED8),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  minimumSize: Size.zero,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  elevation: 0,
                ),
                icon: const Icon(Icons.add, size: 16),
                label: const Text('Log',
                    style:
                        TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        // Summary cards
        Row(
          children: [
            Expanded(
              child: AppCard(
                radius: 16,
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Weekly Avg',
                        style: AppTextStyles.labelSm
                            .copyWith(color: AppColors.onSurfaceVariant)),
                    const SizedBox(height: 4),
                    Text(
                      '${(_summary?.weeklyAverageCalories ?? 0).round()} kcal',
                      style: AppTextStyles.headlineMd,
                    ),
                    Text('/ day',
                        style: AppTextStyles.labelSm
                            .copyWith(color: AppColors.onSurfaceVariant)),
                  ],
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: AppCard(
                radius: 16,
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Goal Achievement',
                        style: AppTextStyles.labelSm
                            .copyWith(color: AppColors.onSurfaceVariant)),
                    const SizedBox(height: 8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(AppRadius.full),
                      child: LinearProgressIndicator(
                        value: (_summary?.goalAchievementPct ?? 0) / 100,
                        backgroundColor: AppColors.surfaceContainerHigh,
                        color: AppColors.primary,
                        minHeight: 10,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${(_summary?.goalAchievementPct ?? 0).round()}%',
                      style: AppTextStyles.headlineMd
                          .copyWith(color: AppColors.primary),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Weight chart ──────────────────────────────────────────────────────
        _buildWeightChart(),
        const SizedBox(height: 16),

        // Recent log entries
        AppCard(
          radius: 20,
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Recent entries', style: AppTextStyles.headlineMd),
              const SizedBox(height: 12),
              if (_logs.isEmpty)
                Text('No entries logged yet.',
                    style: AppTextStyles.bodyMd
                        .copyWith(color: AppColors.onSurfaceVariant))
              else
                ..._logs.take(10).map((log) => _LogRow(log: log)),
            ],
          ),
        ),
        const SizedBox(height: 24),
      ],
    );
  }

  // ── Weight Chart ────────────────────────────────────────────────────────────
  Widget _buildWeightChart() {
    if (_weightHistory.isEmpty) {
      return AppCard(
        radius: 20,
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Row(
              children: [
                const Text('Weight over time',
                    style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: Color(0xFF111827))),
                const Spacer(),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: const Color(0xFF3B82F6).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Text('0 entries',
                      style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF3B82F6))),
                ),
              ],
            ),
            const SizedBox(height: 32),
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: const Color(0xFF3B82F6).withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(Icons.show_chart_rounded,
                  color: Color(0xFF3B82F6), size: 28),
            ),
            const SizedBox(height: 12),
            const Text('No weight data yet',
                style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF111827))),
            const SizedBox(height: 4),
            const Text('Log your weight to track your trend',
                style: TextStyle(fontSize: 12, color: Color(0xFF9CA3AF))),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                key: const ValueKey('progress_log_first_entry_button'),
                onPressed: _openLogSheet,
                icon: const Icon(Icons.add, size: 16),
                label: const Text('Log First Entry'),
                style: OutlinedButton.styleFrom(
                  shape: const StadiumBorder(),
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
              ),
            ),
          ],
        ),
      );
    }

    // Compute Y-range with padding so single points aren't at the chart edge
    final weights = _weightHistory.map((e) => e.weightKg).toList();
    final minW = weights.reduce((a, b) => a < b ? a : b);
    final maxW = weights.reduce((a, b) => a > b ? a : b);
    final range = (maxW - minW).clamp(2.0, double.infinity);
    final padding = range * 0.25;
    final minY = (minW - padding).floorToDouble();
    final maxY = (maxW + padding).ceilToDouble();
    final yInterval = ((maxY - minY) / 4).ceilToDouble().clamp(0.5, 100.0);

    final xMax =
        (_weightHistory.length - 1).toDouble().clamp(1.0, double.infinity);
    final xInterval =
        _weightHistory.length > 6 ? (xMax / 4).ceilToDouble() : 1.0;

    return AppCard(
      radius: 20,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            children: [
              const Text('Weight over time',
                  style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF111827))),
              const Spacer(),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text('${_weightHistory.length} entries',
                    style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: AppColors.primary)),
              ),
            ],
          ),
          const SizedBox(height: 4),
          // Min/max labels
          Row(
            children: [
              Text('Min: ${minW.toStringAsFixed(1)} kg',
                  style:
                      const TextStyle(fontSize: 11, color: Color(0xFF9CA3AF))),
              const SizedBox(width: 12),
              Text('Max: ${maxW.toStringAsFixed(1)} kg',
                  style:
                      const TextStyle(fontSize: 11, color: Color(0xFF9CA3AF))),
            ],
          ),
          const SizedBox(height: 12),
          // Chart
          SizedBox(
            height: 200,
            child: LineChart(
              LineChartData(
                minX: 0,
                maxX: xMax,
                minY: minY,
                maxY: maxY,
                clipData: const FlClipData.all(),
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: yInterval,
                  getDrawingHorizontalLine: (_) => FlLine(
                    color: const Color(0xFFE5E7EB),
                    strokeWidth: 1,
                    dashArray: [4, 4],
                  ),
                ),
                titlesData: FlTitlesData(
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 44,
                      interval: yInterval,
                      getTitlesWidget: (v, meta) {
                        if (v == meta.min || v == meta.max)
                          return const SizedBox.shrink();
                        return Padding(
                          padding: const EdgeInsets.only(right: 4),
                          child: Text(
                            '${v.round()}',
                            style: const TextStyle(
                                fontSize: 10,
                                color: Color(0xFF9CA3AF),
                                fontWeight: FontWeight.w500),
                          ),
                        );
                      },
                    ),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 28,
                      interval: xInterval,
                      getTitlesWidget: (v, meta) {
                        final idx = v.round();
                        if (idx < 0 || idx >= _weightHistory.length) {
                          return const SizedBox.shrink();
                        }
                        // Only show if it's close to an integer index
                        if ((v - idx).abs() > 0.01)
                          return const SizedBox.shrink();
                        return Padding(
                          padding: const EdgeInsets.only(top: 6),
                          child: Text(
                            DateFormat('d MMM')
                                .format(_weightHistory[idx].date),
                            style: const TextStyle(
                                fontSize: 10,
                                color: Color(0xFF9CA3AF),
                                fontWeight: FontWeight.w500),
                          ),
                        );
                      },
                    ),
                  ),
                  topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false)),
                ),
                borderData: FlBorderData(show: false),
                lineTouchData: LineTouchData(
                  touchTooltipData: LineTouchTooltipData(
                    getTooltipItems: (spots) => spots.map((s) {
                      final idx = s.x.round();
                      final date = idx >= 0 && idx < _weightHistory.length
                          ? DateFormat('d MMM').format(_weightHistory[idx].date)
                          : '';
                      return LineTooltipItem(
                        '${s.y.toStringAsFixed(1)} kg\n$date',
                        const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w700,
                            fontSize: 12),
                      );
                    }).toList(),
                  ),
                ),
                lineBarsData: [
                  LineChartBarData(
                    spots: _weightHistory.asMap().entries.map((e) {
                      return FlSpot(e.key.toDouble(), e.value.weightKg);
                    }).toList(),
                    isCurved: _weightHistory.length > 2,
                    curveSmoothness: 0.3,
                    color: AppColors.primary,
                    barWidth: 2.5,
                    dotData: FlDotData(
                      show: true,
                      getDotPainter: (spot, pct, bar, index) =>
                          FlDotCirclePainter(
                        radius: 4,
                        color: Colors.white,
                        strokeColor: AppColors.primary,
                        strokeWidth: 2,
                      ),
                    ),
                    belowBarData: BarAreaData(
                      show: true,
                      gradient: LinearGradient(
                        colors: [
                          AppColors.primary.withValues(alpha: 0.18),
                          AppColors.primary.withValues(alpha: 0.0),
                        ],
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// A compact single-row entry in the history list.
class _LogRow extends StatelessWidget {
  final ProgressLog log;
  const _LogRow({required this.log});

  @override
  Widget build(BuildContext context) {
    final parts = <String>[];
    if (log.weightKg != null)
      parts.add('${log.weightKg!.toStringAsFixed(1)} kg');
    if (log.caloriesConsumed != null) parts.add('${log.caloriesConsumed} kcal');
    if (log.proteinConsumedG != null)
      parts.add('${log.proteinConsumedG}g prot');

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Text(
            DateFormat('d MMM').format(log.date),
            style: AppTextStyles.labelMd
                .copyWith(color: AppColors.onSurfaceVariant, fontSize: 12),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              parts.isEmpty ? 'Entry logged' : parts.join(' · '),
              style: AppTextStyles.bodyMd.copyWith(fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}

/// Bottom sheet form for logging a new progress entry.
class _LogEntrySheet extends StatefulWidget {
  final VoidCallback onSubmitted;
  const _LogEntrySheet({required this.onSubmitted});

  @override
  State<_LogEntrySheet> createState() => _LogEntrySheetState();
}

class _LogEntrySheetState extends State<_LogEntrySheet> {
  final _weightCtrl = TextEditingController();
  final _calCtrl = TextEditingController();
  final _proteinCtrl = TextEditingController();
  final _carbsCtrl = TextEditingController();
  final _fatCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
  bool _submitting = false;
  String? _error;

  @override
  void dispose() {
    _weightCtrl.dispose();
    _calCtrl.dispose();
    _proteinCtrl.dispose();
    _carbsCtrl.dispose();
    _fatCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final weight = double.tryParse(_weightCtrl.text);
    final cal = int.tryParse(_calCtrl.text);
    final protein = int.tryParse(_proteinCtrl.text);
    final carbs = int.tryParse(_carbsCtrl.text);
    final fat = int.tryParse(_fatCtrl.text);

    if (weight == null &&
        cal == null &&
        protein == null &&
        carbs == null &&
        fat == null) {
      setState(() => _error = 'Please fill in at least one value.');
      return;
    }

    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      // POST /api/progress
      await ApiService.instance.post('/api/progress', body: {
        if (weight != null) 'weightKg': weight,
        if (cal != null) 'caloriesConsumed': cal,
        if (protein != null) 'proteinConsumedG': protein,
        if (carbs != null) 'carbsConsumedG': carbs,
        if (fat != null) 'fatConsumedG': fat,
        if (_notesCtrl.text.trim().isNotEmpty) 'notes': _notesCtrl.text.trim(),
      });
      widget.onSubmitted();
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Unable to log entry. Please try again.');
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.of(context).viewInsets.bottom;
    return Padding(
      padding: EdgeInsets.fromLTRB(20, 24, 20, 24 + bottom),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Log a new entry', style: AppTextStyles.headlineMd),
            const SizedBox(height: 16),
            if (_error != null)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.error.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(AppRadius.dflt),
                ),
                child: Text(_error!,
                    key: const ValueKey('progress_log_error_text'),
                    style:
                        AppTextStyles.bodyMd.copyWith(color: AppColors.error)),
              ),
            Row(
              children: [
                Expanded(
                    child: _NumberField('Weight (kg)', _weightCtrl,
                        decimal: true,
                        fieldKey: const ValueKey('progress_log_weight_field'))),
                const SizedBox(width: 12),
                Expanded(
                    child: _NumberField('Calories', _calCtrl,
                        fieldKey: const ValueKey('progress_log_calories_field'))),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                    child: _NumberField('Protein (g)', _proteinCtrl,
                        fieldKey: const ValueKey('progress_log_protein_field'))),
                const SizedBox(width: 12),
                Expanded(
                    child: _NumberField('Carbs (g)', _carbsCtrl,
                        fieldKey: const ValueKey('progress_log_carbs_field'))),
                const SizedBox(width: 12),
                Expanded(
                    child: _NumberField('Fat (g)', _fatCtrl,
                        fieldKey: const ValueKey('progress_log_fat_field'))),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              key: const ValueKey('progress_log_notes_field'),
              controller: _notesCtrl,
              maxLines: 2,
              decoration: const InputDecoration(
                labelText: 'Notes (optional)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                key: const ValueKey('progress_log_submit_button'),
                onPressed: _submitting ? null : _submit,
                child: _submitting
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white))
                    : const Text('Log Entry'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NumberField extends StatelessWidget {
  final String label;
  final TextEditingController controller;
  final bool decimal;
  final Key? fieldKey;
  const _NumberField(this.label, this.controller,
      {this.decimal = false, this.fieldKey});

  @override
  Widget build(BuildContext context) {
    return TextField(
      key: fieldKey,
      controller: controller,
      keyboardType: TextInputType.numberWithOptions(decimal: decimal),
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      ),
    );
  }
}
