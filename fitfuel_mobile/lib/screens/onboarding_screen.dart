import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _controller = PageController();
  int _page = 0;

  void _finish() {
    Navigator.of(context).pushReplacementNamed('/login');
  }

  void _next() {
    if (_page < 2) {
      _controller.nextPage(
          duration: const Duration(milliseconds: 300), curve: Curves.easeOut);
    } else {
      _finish();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.marginMobile, vertical: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    key: const ValueKey('onboarding_skip_button'),
                    onPressed: _finish,
                    child: Text('Skip',
                        style: AppTextStyles.labelMd
                            .copyWith(color: AppColors.onSurfaceVariant)),
                  ),
                ],
              ),
            ),
            Expanded(
              child: PageView(
                controller: _controller,
                onPageChanged: (i) => setState(() => _page = i),
                children: const [
                  _TargetsSlide(),
                  _MatchSlide(),
                  _OrderSlide(),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.marginMobile, vertical: 24),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: List.generate(3, (i) {
                      final active = i == _page;
                      return AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        margin: const EdgeInsets.symmetric(horizontal: 4),
                        width: active ? 24 : 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: active
                              ? AppColors.primary
                              : AppColors.surfaceContainerHigh,
                          borderRadius: BorderRadius.circular(AppRadius.full),
                        ),
                      );
                    }),
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton(
                    key: const ValueKey('onboarding_next_button'),
                    onPressed: _next,
                    style: ElevatedButton.styleFrom(
                        shape: RoundedRectangleBorder(
                            borderRadius:
                                BorderRadius.circular(AppRadius.full))),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(_page == 2 ? 'Get Started' : 'Next'),
                        const SizedBox(width: 8),
                        const Icon(Icons.arrow_forward, size: 18),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SlideScaffold extends StatelessWidget {
  final Widget illustration;
  final String title;
  final String subtitle;
  const _SlideScaffold(
      {required this.illustration,
      required this.title,
      required this.subtitle});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.marginMobile),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Expanded(child: Center(child: illustration)),
          Text(title,
              textAlign: TextAlign.center,
              style: AppTextStyles.headlineLgMobile),
          const SizedBox(height: 12),
          Text(subtitle,
              textAlign: TextAlign.center,
              style: AppTextStyles.bodyMd
                  .copyWith(color: AppColors.onSurfaceVariant)),
          const Spacer(),
        ],
      ),
    );
  }
}

class _TargetsSlide extends StatelessWidget {
  const _TargetsSlide();
  @override
  Widget build(BuildContext context) {
    return _SlideScaffold(
      illustration: Container(
        width: 220,
        height: 220,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: const LinearGradient(
            colors: [AppColors.primaryContainer, AppColors.primary],
          ),
        ),
        child: const Icon(Icons.track_changes, color: Colors.white, size: 84),
      ),
      title: 'Get your personal nutrition targets',
      subtitle:
          'Precision AI crafts the perfect macro balance tailored to your unique physiology and goals.',
    );
  }
}

class _MatchSlide extends StatelessWidget {
  const _MatchSlide();
  @override
  Widget build(BuildContext context) {
    return _SlideScaffold(
      illustration: Container(
        width: 260,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(AppRadius.lg),
          boxShadow: kCardShadowLevel2,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 100,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(AppRadius.dflt),
                gradient: const LinearGradient(
                  colors: [AppColors.coralStart, AppColors.coralEnd],
                ),
              ),
              child: const Icon(Icons.set_meal, color: Colors.white, size: 40),
            ),
            const SizedBox(height: 12),
            Text('Miso Glazed Salmon',
                style: AppTextStyles.headlineMd.copyWith(fontSize: 16)),
            Text('Bistro Select',
                style: AppTextStyles.labelSm
                    .copyWith(color: AppColors.onSurfaceVariant)),
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.check_circle,
                    color: AppColors.primary, size: 16),
                const SizedBox(width: 4),
                Text('Matches Goal · High Protein · 500 kcal',
                    style: AppTextStyles.labelSm
                        .copyWith(color: AppColors.onSurfaceVariant)),
              ],
            ),
          ],
        ),
      ),
      title: 'Get restaurant meals that match your goals',
      subtitle:
          'Our AI cross-references local menus with your nutritional targets to find perfect options when dining out.',
    );
  }
}

class _OrderSlide extends StatelessWidget {
  const _OrderSlide();
  @override
  Widget build(BuildContext context) {
    return _SlideScaffold(
      illustration: Container(
        width: 220,
        height: 220,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: AppColors.secondaryContainer.withOpacity(0.15),
        ),
        child: const Icon(Icons.delivery_dining,
            color: AppColors.secondary, size: 84),
      ),
      title: 'Order in one tap on Swiggy/Zomato',
      subtitle:
          'Seamlessly connect your food delivery apps for instant, AI-approved meal choices delivered to your door.',
    );
  }
}
