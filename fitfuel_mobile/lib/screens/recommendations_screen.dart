import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

/// Meal type tab indices
const _mealTypeCodes = ['BREAKFAST', 'LUNCH', 'DINNER', 'SNACK'];
const _mealTypeLabels = ['Breakfast', 'Lunch', 'Dinner', 'Snack'];

class RecommendationsScreen extends StatefulWidget {
  const RecommendationsScreen({super.key});

  @override
  State<RecommendationsScreen> createState() => _RecommendationsScreenState();
}

class _RecommendationsScreenState extends State<RecommendationsScreen> {
  int _mealTypeIndex = 1; // default LUNCH
  List<Recommendation> _recommendations = [];
  bool _loading = false;
  String? _error;
  String? _orderingMealId; // which meal is currently being ordered

  @override
  void initState() {
    super.initState();
    _loadRecommendations();
  }

  Future<void> _loadRecommendations() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      // GET /api/recommendations?mealType=LUNCH → { recommendations: [...] }
      final data = await ApiService.instance.get(
        '/api/recommendations',
        query: {'mealType': _mealTypeCodes[_mealTypeIndex]},
      );
      final list = (data['recommendations'] as List)
          .map((e) => Recommendation.fromJson(e as Map<String, dynamic>))
          .toList();
      if (mounted) setState(() => _recommendations = list);
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.statusCode == 400) {
        // No health profile — redirect to assessment
        Navigator.of(context).pushReplacementNamed('/health-weight');
        return;
      }
      setState(() => _error = e.message);
    } catch (e) {
      if (mounted)
        setState(
            () => _error = 'Unable to load recommendations. Please try again.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _placeOrder(Recommendation rec, String platform) async {
    setState(() => _orderingMealId = rec.mealId);
    try {
      // POST /api/orders returns { order: {...}, deepLink: "https://..." }
      final data = await ApiService.instance.post('/api/orders', body: {
        'mealId': rec.mealId,
        'platform': platform,
      });
      final result = OrderResult.fromJson(data as Map<String, dynamic>);
      final httpsUri = Uri.parse(result.deepLink);

      bool launched = false;
      try {
        // Use externalNonBrowserApplication to force Android to open the native app (via App Links)
        launched = await launchUrl(httpsUri,
            mode: LaunchMode.externalNonBrowserApplication);
      } catch (_) {}

      // Fallback to regular external application (opens Chrome if app not installed)
      if (!launched) {
        try {
          launched =
              await launchUrl(httpsUri, mode: LaunchMode.externalApplication);
        } catch (_) {}
      }

      if (!launched && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content: Text(
                  'Could not open ${platform == 'SWIGGY' ? 'Swiggy' : 'Zomato'}')),
        );
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: AppColors.error),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('Unable to start order. Please try again.')),
        );
      }
    } finally {
      if (mounted) setState(() => _orderingMealId = null);
    }
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
        title: const Text('Recommendations',
            style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                color: Color(0xFF111827))),
      ),
      body: SafeArea(
        top: false,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.marginMobile, vertical: 12),
              child: PillTabSelector(
                tabs: _mealTypeLabels,
                selectedIndex: _mealTypeIndex,
                onChanged: (i) {
                  setState(() {
                    _mealTypeIndex = i;
                    _recommendations = [];
                  });
                  _loadRecommendations();
                },
              ),
            ),
            Expanded(child: _buildBody()),
          ],
        ),
      ),
      bottomNavigationBar: FitFuelBottomNav(
        currentIndex: 1,
        onTap: (i) {
          if (i == 0) Navigator.of(context).pushReplacementNamed('/dashboard');
          if (i == 2) Navigator.of(context).pushReplacementNamed('/progress');
          if (i == 3) Navigator.of(context).pushReplacementNamed('/profile');
        },
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.wifi_off_rounded,
                  size: 48, color: AppColors.outline),
              const SizedBox(height: 16),
              Text(_error!,
                  textAlign: TextAlign.center,
                  style: AppTextStyles.bodyMd
                      .copyWith(color: AppColors.onSurfaceVariant)),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                key: const ValueKey('recommendations_retry_button'),
                onPressed: _loadRecommendations,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }
    if (_recommendations.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: const Icon(Icons.restaurant_rounded,
                    color: AppColors.primary, size: 32),
              ),
              const SizedBox(height: 16),
              Text(
                'No meals found for ${_mealTypeLabels[_mealTypeIndex]} yet.',
                textAlign: TextAlign.center,
                style: AppTextStyles.bodyMd
                    .copyWith(color: AppColors.onSurfaceVariant),
              ),
            ],
          ),
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.marginMobile, vertical: 8),
      itemCount: _recommendations.length + 1,
      itemBuilder: (ctx, i) {
        if (i == 0) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Hero banner
              Container(
                margin: const EdgeInsets.only(bottom: 16),
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF2A9D58), Color(0xFF006C4D)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.25),
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
                          const Text('AI Picks for you',
                              style: TextStyle(
                                  color: Colors.white70,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w500)),
                          const SizedBox(height: 2),
                          Text(
                            _mealTypeLabels[_mealTypeIndex],
                            style: const TextStyle(
                                color: Colors.white,
                                fontSize: 22,
                                fontWeight: FontWeight.w800),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                              'Ranked by calorie accuracy, protein quality & budget',
                              style: TextStyle(
                                  color: Colors.white60, fontSize: 11)),
                        ],
                      ),
                    ),
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: const Icon(Icons.auto_awesome_rounded,
                          color: Colors.white, size: 26),
                    ),
                  ],
                ),
              ),
            ],
          );
        }
        final rec = _recommendations[i - 1];
        return Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: _RecommendationCard(
            rec: rec,
            isOrdering: _orderingMealId == rec.mealId,
            onOrderSwiggy: () => _placeOrder(rec, 'SWIGGY'),
            onOrderZomato: () => _placeOrder(rec, 'ZOMATO'),
          ),
        );
      },
    );
  }
}

class _RecommendationCard extends StatefulWidget {
  final Recommendation rec;
  final bool isOrdering;
  final VoidCallback onOrderSwiggy;
  final VoidCallback onOrderZomato;

  const _RecommendationCard({
    required this.rec,
    required this.isOrdering,
    required this.onOrderSwiggy,
    required this.onOrderZomato,
  });

  @override
  State<_RecommendationCard> createState() => _RecommendationCardState();
}

class _RecommendationCardState extends State<_RecommendationCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final meal = widget.rec.meal;
    final bd = widget.rec.breakdown;

    return AppCard(
      key: ValueKey('recommendation_card_${widget.rec.mealId}'),
      radius: 20,
      padding:
          EdgeInsets.zero, // remove padding so the image bleeds to the edges
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Meal photo ──────────────────────────────────────────────────────
          ClipRRect(
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
            child: meal.imageUrl != null
                ? Image.network(
                    meal.imageUrl!,
                    height: 180,
                    width: double.infinity,
                    fit: BoxFit.cover,
                    loadingBuilder: (ctx, child, progress) {
                      if (progress == null) return child;
                      return Container(
                        height: 180,
                        color: AppColors.surfaceContainerHigh,
                        child: const Center(
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      );
                    },
                    errorBuilder: (ctx, error, stack) => _ImageFallback(),
                  )
                : _ImageFallback(),
          ),
          // ── Card body ───────────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header row: match score + meal type
                Row(
                  children: [
                    MatchScoreChip(score: widget.rec.score.round()),
                    const Spacer(),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color:
                            AppColors.primaryContainer.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(AppRadius.full),
                      ),
                      child: Text(
                        meal.mealType,
                        style: AppTextStyles.labelSm
                            .copyWith(color: AppColors.primary),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(meal.name,
                    style: AppTextStyles.headlineMd.copyWith(fontSize: 17)),
                const SizedBox(height: 2),
                Text('${meal.cuisine} Cuisine',
                    style: AppTextStyles.labelMd
                        .copyWith(color: AppColors.onSurfaceVariant)),
                const SizedBox(height: 12),
                // Macro chips
                Wrap(
                  spacing: 16,
                  runSpacing: 6,
                  children: [
                    _StatChip(Icons.fitness_center, '${meal.proteinG}g Pro'),
                    _StatChip(Icons.grass, '${meal.carbsG}g Carbs'),
                    _StatChip(Icons.water_drop, '${meal.fatG}g Fat'),
                    _StatChip(
                        Icons.local_fire_department, '${meal.calories} kcal'),
                  ],
                ),
                const SizedBox(height: 8),
                // Expandable breakdown
                InkWell(
                  key: ValueKey('recommendation_expand_${widget.rec.mealId}'),
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
                      child: Column(
                        children: [
                          _BreakdownRow('Calorie Accuracy', bd.calorieAccuracy),
                          _BreakdownRow('Protein Quality', bd.proteinQuality),
                          _BreakdownRow('Budget Fit', bd.budgetFit),
                          _BreakdownRow('Health Score', bd.healthScore),
                        ],
                      ),
                    ),
                  ),
                const SizedBox(height: 14),
                // Order buttons — Swiggy orange + Zomato red (brand colors)
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        key: ValueKey('recommendation_order_swiggy_${widget.rec.mealId}'),
                        onPressed:
                            widget.isOrdering ? null : widget.onOrderSwiggy,
                        style: ElevatedButton.styleFrom(
                          backgroundColor:
                              const Color(0xFFFC8019), // Swiggy orange
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(24),
                          ),
                        ),
                        icon: widget.isOrdering
                            ? const SizedBox(
                                height: 14,
                                width: 14,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2, color: Colors.white))
                            : const Icon(Icons.local_fire_department_rounded,
                                size: 16),
                        label: const Text('Swiggy'),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: ElevatedButton.icon(
                        key: ValueKey('recommendation_order_zomato_${widget.rec.mealId}'),
                        onPressed:
                            widget.isOrdering ? null : widget.onOrderZomato,
                        style: ElevatedButton.styleFrom(
                          backgroundColor:
                              const Color(0xFFE23744), // Zomato red
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(24),
                          ),
                        ),
                        icon: widget.isOrdering
                            ? const SizedBox(
                                height: 14,
                                width: 14,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2, color: Colors.white))
                            : const Icon(Icons.restaurant_rounded, size: 16),
                        label: const Text('Zomato'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Text(
                  'Opens the platform\'s own search — complete checkout there.',
                  style:
                      AppTextStyles.labelSm.copyWith(color: AppColors.outline),
                ),
              ],
            ),
          ), // end Padding (card body)
        ],
      ),
    );
  }
}

class _StatChip extends StatelessWidget {
  final IconData icon;
  final String label;
  const _StatChip(this.icon, this.label);

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: AppColors.onSurfaceVariant),
        const SizedBox(width: 4),
        Text(label,
            style: AppTextStyles.labelSm
                .copyWith(color: AppColors.onSurfaceVariant)),
      ],
    );
  }
}

class _BreakdownRow extends StatelessWidget {
  final String label;
  final double value;
  const _BreakdownRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: AppTextStyles.labelMd),
          Text('${value.round()}%',
              style: AppTextStyles.labelMd.copyWith(
                  color: AppColors.primary, fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

/// Placeholder shown when a meal has no imageUrl, or when Image.network fails to load.
class _ImageFallback extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      height: 180,
      width: double.infinity,
      color: AppColors.surfaceContainerHigh,
      child: const Center(
        child: Icon(
          Icons.restaurant_rounded,
          size: 56,
          color: AppColors.outline,
        ),
      ),
    );
  }
}
