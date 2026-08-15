import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  HealthProfile? _profile;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await ApiService.instance.get('/api/health-profile');
      if (mounted) {
        setState(() {
          _profile =
              HealthProfile.fromJson(data['profile'] as Map<String, dynamic>);
        });
      }
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.statusCode == 404) {
        Navigator.of(context).pushReplacementNamed('/health-weight');
        return;
      }
      setState(() => _error = e.message);
    } catch (_) {
      if (mounted)
        setState(() => _error = 'Unable to load dashboard. Please try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  int? _calorieTarget(HealthProfile p) {
    if (p.tdee == null) return null;
    const adj = {
      'WEIGHT_LOSS': -500,
      'WEIGHT_GAIN': 400,
      'MUSCLE_GAIN': 300,
      'MAINTENANCE': 0,
    };
    return (p.tdee! + (adj[p.fitnessGoal] ?? 0))
        .clamp(1200, double.infinity)
        .round();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7FAF8),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        surfaceTintColor: Colors.transparent,
        centerTitle: false,
        automaticallyImplyLeading: false,
        title: Row(
          children: [
            Container(
              width: 34,
              height: 34,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(10),
                gradient: const LinearGradient(
                  colors: [Color(0xFF2A9D58), Color(0xFF006C4D)],
                ),
              ),
              child: const Icon(Icons.bolt, color: Colors.white, size: 18),
            ),
            const SizedBox(width: 10),
            const Text('FitFuel',
                style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFF111827))),
          ],
        ),
        actions: [
          IconButton(
            key: const ValueKey('dashboard_notifications_button'),
            icon: Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: const Color(0xFFF3F4F6),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.notifications_outlined,
                  color: Color(0xFF374151), size: 20),
            ),
            onPressed: () {},
          ),
          const SizedBox(width: 4),
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: GestureDetector(
              key: const ValueKey('dashboard_profile_avatar_button'),
              onTap: () => Navigator.of(context).pushNamed('/profile'),
              child: Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF2A9D58), Color(0xFF006C4D)],
                  ),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.person_rounded,
                    color: Colors.white, size: 20),
              ),
            ),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _buildError()
              : _buildBody(),
      bottomNavigationBar: FitFuelBottomNav(
        currentIndex: 0,
        onTap: (i) {
          if (i == 1)
            Navigator.of(context).pushReplacementNamed('/recommendations');
          if (i == 2) Navigator.of(context).pushNamed('/chat');
          if (i == 3) Navigator.of(context).pushReplacementNamed('/progress');
          if (i == 4) Navigator.of(context).pushReplacementNamed('/profile');
        },
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.wifi_off_rounded,
                size: 56, color: Color(0xFFD1D5DB)),
            const SizedBox(height: 16),
            Text(_error!,
                textAlign: TextAlign.center,
                style: AppTextStyles.bodyMd
                    .copyWith(color: AppColors.onSurfaceVariant)),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              key: const ValueKey('dashboard_retry_button'),
              onPressed: _loadProfile,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
              style: ElevatedButton.styleFrom(shape: const StadiumBorder()),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBody() {
    final p = _profile!;
    final calTarget = _calorieTarget(p);

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Hero banner ──────────────────────────────────────────────────
          GradientHeroCard(
            colors: const [Color(0xFF2A9D58), Color(0xFF006C4D)],
            child: Padding(
              padding: const EdgeInsets.all(22),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Welcome back 👋',
                                style: TextStyle(
                                    color: Colors.white70,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500)),
                            const SizedBox(height: 2),
                            Text(
                              'Your daily target',
                              style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 20,
                                  fontWeight: FontWeight.w800),
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(AppRadius.full),
                        ),
                        child: Text(
                          p.fitnessGoal.replaceAll('_', ' '),
                          style: const TextStyle(
                              color: Colors.white,
                              fontSize: 11,
                              fontWeight: FontWeight.w700),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        calTarget != null ? '$calTarget' : '—',
                        style: const TextStyle(
                            color: Colors.white,
                            fontSize: 48,
                            fontWeight: FontWeight.w900,
                            height: 1),
                      ),
                      const Padding(
                        padding: EdgeInsets.only(bottom: 8, left: 4),
                        child: Text('kcal/day',
                            style: TextStyle(
                                color: Colors.white70,
                                fontSize: 14,
                                fontWeight: FontWeight.w500)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  // Mini macro chips
                  Row(
                    children: [
                      _heroBadge('🥩', '${p.proteinTargetG?.round() ?? 0}g',
                          'Protein'),
                      const SizedBox(width: 8),
                      _heroBadge('🌾', '${p.carbTargetG ?? 0}g', 'Carbs'),
                      const SizedBox(width: 8),
                      _heroBadge(
                          '🥑', '${p.fatTargetG?.round() ?? 0}g', 'Fats'),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // ── Stats row ───────────────────────────────────────────────────
          Row(
            children: [
              StatChip(
                label: 'BMR',
                value: p.bmr != null ? '${p.bmr!.round()}' : '—',
                color: const Color(0xFF8B5CF6),
                icon: Icons.bolt_rounded,
              ),
              const SizedBox(width: 10),
              StatChip(
                label: 'TDEE',
                value: p.tdee != null ? '${p.tdee!.round()}' : '—',
                color: const Color(0xFF3B82F6),
                icon: Icons.directions_run_rounded,
              ),
              const SizedBox(width: 10),
              StatChip(
                label: 'BMI',
                value: p.bmi != null ? p.bmi!.toStringAsFixed(1) : '—',
                color: const Color(0xFFF59E0B),
                icon: Icons.monitor_weight_outlined,
              ),
            ],
          ),
          const SizedBox(height: 20),

          // ── Daily macros card ────────────────────────────────────────────
          AppCard(
            radius: 20,
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Text('Daily Macros',
                        style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                            color: Color(0xFF111827))),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: const Color(0xFF2A9D58).withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(AppRadius.full),
                      ),
                      child: const Text('Daily targets',
                          style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFF2A9D58))),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                MacroProgressRow(
                  label: 'Protein',
                  current: p.proteinTargetG?.round() ?? 0,
                  target: p.proteinTargetG?.round() ?? 1,
                  color: const Color(0xFF2A9D58),
                ),
                MacroProgressRow(
                  label: 'Carbohydrates',
                  current: p.carbTargetG ?? 0,
                  target: p.carbTargetG ?? 1,
                  color: const Color(0xFF3B82F6),
                ),
                MacroProgressRow(
                  label: 'Fats',
                  current: p.fatTargetG?.round() ?? 0,
                  target: p.fatTargetG?.round() ?? 1,
                  color: const Color(0xFFF59E0B),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // ── Quick nav label ──────────────────────────────────────────────
          const Text('Quick Access',
              style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF111827))),
          const SizedBox(height: 12),

          // 2×2 grid of quick action cards
          Row(
            children: [
              _QuickCard(
                cardKey: const ValueKey('dashboard_quick_recommendations'),
                icon: Icons.auto_awesome_rounded,
                label: 'Recommendations',
                sub: 'Ranked meals',
                gradient: const [Color(0xFF2A9D58), Color(0xFF006C4D)],
                onTap: () =>
                    Navigator.of(context).pushNamed('/recommendations'),
              ),
              const SizedBox(width: 12),
              _QuickCard(
                cardKey: const ValueKey('dashboard_quick_meal_plan'),
                icon: Icons.calendar_month_rounded,
                label: 'Meal Plan',
                sub: '7-day plan',
                gradient: const [Color(0xFF8B5CF6), Color(0xFF6D28D9)],
                onTap: () => Navigator.of(context).pushNamed('/weekly-plan'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _QuickCard(
                cardKey: const ValueKey('dashboard_quick_ai_coach'),
                icon: Icons.chat_bubble_rounded,
                label: 'AI Coach',
                sub: 'Ask anything',
                gradient: const [Color(0xFF3B82F6), Color(0xFF1D4ED8)],
                onTap: () => Navigator.of(context).pushNamed('/chat'),
              ),
              const SizedBox(width: 12),
              _QuickCard(
                cardKey: const ValueKey('dashboard_quick_progress'),
                icon: Icons.show_chart_rounded,
                label: 'Progress',
                sub: 'Track trends',
                gradient: const [Color(0xFFF59E0B), Color(0xFFD97706)],
                onTap: () => Navigator.of(context).pushNamed('/progress'),
              ),
            ],
          ),

          if (p.aiExplanation != null) ...[
            const SizedBox(height: 20),
            AppCard(
              radius: 16,
              padding: const EdgeInsets.all(16),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(10),
                      gradient: const LinearGradient(
                        colors: [Color(0xFF2A9D58), Color(0xFF006C4D)],
                      ),
                    ),
                    child: const Icon(Icons.smart_toy_rounded,
                        color: Colors.white, size: 18),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('AI Coach says',
                            style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                color: Color(0xFF111827))),
                        const SizedBox(height: 4),
                        Text(p.aiExplanation!,
                            style: const TextStyle(
                                fontSize: 13,
                                color: Color(0xFF6B7280),
                                height: 1.5)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _heroBadge(String emoji, String value, String label) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.15),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('$emoji $value',
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w800)),
            Text(label,
                style: const TextStyle(
                    color: Colors.white60,
                    fontSize: 10,
                    fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Quick action card
// ─────────────────────────────────────────────────────────────────────────────

class _QuickCard extends StatelessWidget {
  final Key? cardKey;
  final IconData icon;
  final String label;
  final String sub;
  final List<Color> gradient;
  final VoidCallback onTap;
  const _QuickCard({
    this.cardKey,
    required this.icon,
    required this.label,
    required this.sub,
    required this.gradient,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: GestureDetector(
        key: cardKey,
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: LinearGradient(
                colors: gradient,
                begin: Alignment.topLeft,
                end: Alignment.bottomRight),
            borderRadius: BorderRadius.circular(18),
            boxShadow: [
              BoxShadow(
                  color: gradient.first.withValues(alpha: 0.3),
                  offset: const Offset(0, 6),
                  blurRadius: 14)
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: Colors.white, size: 20),
              ),
              const SizedBox(height: 12),
              Text(label,
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                      fontWeight: FontWeight.w800)),
              Text(sub,
                  style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 11,
                      fontWeight: FontWeight.w500)),
            ],
          ),
        ),
      ),
    );
  }
}
