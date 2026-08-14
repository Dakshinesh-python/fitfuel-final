import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

class WeeklyMealPlanScreen extends StatefulWidget {
  const WeeklyMealPlanScreen({super.key});

  @override
  State<WeeklyMealPlanScreen> createState() => _WeeklyMealPlanScreenState();
}

class _WeeklyMealPlanScreenState extends State<WeeklyMealPlanScreen> {
  int _selectedDay = 0; // 0 = Monday

  MealPlan? _plan;
  bool _loading = true;
  bool _generating = false;
  String? _error;

  static const _days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  static const _mealOrder = ['BREAKFAST', 'LUNCH', 'SNACK', 'DINNER'];

  @override
  void initState() {
    super.initState();
    _fetchCurrent();
  }

  Future<void> _fetchCurrent() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final data = await ApiService.instance.get('/api/meal-plans/current');
      if (mounted) {
        setState(() {
          _plan = MealPlan.fromJson(data['mealPlan'] as Map<String, dynamic>);
        });
      }
    } on ApiException catch (e) {
      // 404 means no plan yet — that is fine, show empty state
      if (e.statusCode != 404 && mounted) {
        setState(() => _error = e.message);
      }
    } catch (_) {
      if (mounted) setState(() => _error = 'Unable to load meal plan.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _generate() async {
    setState(() {
      _generating = true;
      _error = null;
    });
    try {
      final data =
          await ApiService.instance.post('/api/meal-plans/generate', body: {});
      if (mounted) {
        setState(() {
          _plan = MealPlan.fromJson(data['mealPlan'] as Map<String, dynamic>);
        });
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() => _error = e.message);
      }
    } catch (_) {
      if (mounted) {
        setState(() => _error =
            'Could not generate meal plan. Complete your health assessment first.');
      }
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  List<MealPlanItem> get _dayItems {
    if (_plan == null) return [];
    return _plan!.items.where((item) => item.dayOfWeek == _selectedDay).toList()
      ..sort((a, b) => _mealOrder
          .indexOf(a.mealType)
          .compareTo(_mealOrder.indexOf(b.mealType)));
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
        title: const Text('Meal Plan',
            style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                color: Color(0xFF111827))),
        actions: [
          if (!_generating)
            IconButton(
              icon: const Icon(Icons.auto_awesome_rounded,
                  color: Color(0xFF2A9D58)),
              tooltip: 'Regenerate',
              onPressed: _generate,
            )
          else
            const Padding(
              padding: EdgeInsets.all(12),
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ),
        ],
      ),
      body: SafeArea(
        top: false,
        child: _loading
            ? const Center(child: CircularProgressIndicator())
            : _buildBody(),
      ),
      bottomNavigationBar: FitFuelBottomNav(
        currentIndex: 1,
        onTap: (i) {
          if (i == 0) Navigator.of(context).pushReplacementNamed('/dashboard');
          if (i == 2) Navigator.of(context).pushNamed('/chat');
          if (i == 3) Navigator.of(context).pushReplacementNamed('/progress');
          if (i == 4) Navigator.of(context).pushReplacementNamed('/profile');
        },
      ),
    );
  }

  Widget _buildBody() {
    return ListView(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.marginMobile, vertical: 16),
      children: [
        // Header
        Text('Weekly Plan', style: AppTextStyles.headlineLgMobile),
        const SizedBox(height: 4),
        Text(
          'Your personalized AI-matched nutrition for the week.',
          style:
              AppTextStyles.bodyMd.copyWith(color: AppColors.onSurfaceVariant),
        ),
        const SizedBox(height: 16),

        // Error
        if (_error != null) ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.error.withOpacity(0.1),
              borderRadius: BorderRadius.circular(AppRadius.dflt),
            ),
            child: Text(_error!,
                style: AppTextStyles.bodyMd.copyWith(color: AppColors.error)),
          ),
          const SizedBox(height: 12),
        ],

        // No plan state
        if (_plan == null && !_generating) ...[
          const SizedBox(height: 40),
          Center(
            child: Column(
              children: [
                Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(colors: [
                      Color(0xFF5b21b6),
                      Color(0xFF7c3aed),
                    ]),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Icon(Icons.calendar_month_rounded,
                      color: Colors.white, size: 36),
                ),
                const SizedBox(height: 16),
                Text('No meal plan yet',
                    style: AppTextStyles.headlineMd
                        .copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                Text(
                  'Generate a personalized 7-day plan\nbased on your nutrition goals.',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.bodyMd
                      .copyWith(color: AppColors.onSurfaceVariant),
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: _generate,
                  icon: const Icon(Icons.auto_awesome),
                  label: const Text('Generate My Plan'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 24, vertical: 14),
                    shape: const StadiumBorder(),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 40),
        ],

        // Plan loaded
        if (_plan != null || _generating) ...[
          // Day selector
          SizedBox(
            height: 64,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: _days.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, i) {
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
                        Text(
                          _days[i],
                          style: AppTextStyles.labelSm.copyWith(
                              color: selected
                                  ? Colors.white
                                  : AppColors.onSurfaceVariant),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${i + 11}', // approximate date display
                          style: AppTextStyles.bodyMd.copyWith(
                              fontWeight: FontWeight.w700,
                              color: selected
                                  ? Colors.white
                                  : AppColors.onSurface),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 20),

          // Meal cards for selected day
          if (_generating)
            const Center(
              child: Padding(
                padding: EdgeInsets.symmetric(vertical: 40),
                child: Column(
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 16),
                    Text('Generating your plan…'),
                  ],
                ),
              ),
            )
          else if (_dayItems.isEmpty)
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 32),
                child: Text(
                  'No meals for this day.',
                  style: AppTextStyles.bodyMd
                      .copyWith(color: AppColors.onSurfaceVariant),
                ),
              ),
            )
          else
            ..._dayItems.map((item) => Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: _MealPlanCard(item: item),
                )),

          const SizedBox(height: 12),

          // Regenerate button
          OutlinedButton.icon(
            onPressed: _generating ? null : _generate,
            icon: const Icon(Icons.auto_awesome, size: 18),
            label: const Text('Regenerate Plan'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14),
              shape: const StadiumBorder(),
            ),
          ),
          const SizedBox(height: 24),
        ],
      ],
    );
  }
}

// ─── Meal card ────────────────────────────────────────────────────────────────

class _MealPlanCard extends StatelessWidget {
  final MealPlanItem item;
  const _MealPlanCard({required this.item});

  Color _scoreColor(double score) {
    if (score >= 95) return const Color(0xFF2A9D58);
    if (score >= 80) return const Color(0xFFF59E0B);
    return const Color(0xFFEF4444);
  }

  @override
  Widget build(BuildContext context) {
    final meal = item.meal;
    final score = item.matchScore.round();
    final label = {
          'BREAKFAST': 'Breakfast',
          'LUNCH': 'Lunch',
          'SNACK': 'Snack',
          'DINNER': 'Dinner',
        }[item.mealType] ??
        item.mealType;

    return AppCard(
      radius: 18,
      padding: EdgeInsets.zero,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Image
          ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(18)),
            child: Stack(
              children: [
                if (meal.imageUrl != null)
                  Image.network(
                    meal.imageUrl!,
                    height: 140,
                    width: double.infinity,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => _placeholder(),
                  )
                else
                  _placeholder(),
                // Gradient overlay
                Positioned.fill(
                  child: DecoratedBox(
                    decoration: const BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [Colors.transparent, Color(0xBB000000)],
                      ),
                    ),
                  ),
                ),
                // Score badge
                Positioned(
                  top: 10,
                  right: 10,
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: _scoreColor(item.matchScore),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      '$score% Match',
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.w700),
                    ),
                  ),
                ),
                // Meal type badge
                Positioned(
                  top: 10,
                  left: 10,
                  child: Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.black.withOpacity(0.45),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      label,
                      style: const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                          fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
                // Name at bottom
                Positioned(
                  bottom: 10,
                  left: 12,
                  right: 12,
                  child: Text(
                    meal.name,
                    style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        shadows: [
                          Shadow(
                              offset: Offset(0, 1),
                              blurRadius: 4,
                              color: Colors.black54)
                        ]),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),

          // Body
          Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${meal.restaurant} · ${meal.cuisine}',
                  style: AppTextStyles.labelSm
                      .copyWith(color: AppColors.onSurfaceVariant),
                ),
                const SizedBox(height: 10),
                // Macro chips
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    _chip('${meal.calories} kcal', const Color(0xFFF59E0B)),
                    _chip('${meal.proteinG}g Pro', const Color(0xFF2A9D58)),
                    _chip('${meal.carbsG}g Carbs', const Color(0xFF3B82F6)),
                    _chip('${meal.fatG}g Fat', const Color(0xFF8B5CF6)),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _placeholder() => Container(
        height: 140,
        color: AppColors.surfaceContainerHigh,
        child: const Center(
          child: Icon(Icons.restaurant_rounded,
              size: 40, color: AppColors.outline),
        ),
      );

  Widget _chip(String label, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: const TextStyle(
              color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600),
        ),
      );
}
