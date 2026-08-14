import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscure = true;
  bool _loading = false;
  bool _wakingUp = false;
  Timer? _wakeTimer;
  String? _error;

  @override
  void dispose() {
    _wakeTimer?.cancel();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _wakingUp = false;
      _error = null;
    });

    _wakeTimer?.cancel();
    _wakeTimer = Timer(const Duration(seconds: 4), () {
      if (mounted) setState(() => _wakingUp = true);
    });

    try {
      await AuthService.instance.login(
        email: _emailController.text.trim(),
        password: _passwordController.text,
      );
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed('/dashboard');
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (e) {
      setState(() => _error = 'Something went wrong. Please try again.');
    } finally {
      _wakeTimer?.cancel();
      if (mounted) {
        setState(() {
          _loading = false;
          _wakingUp = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFAF9F6),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Top hero / branding section
              Container(
                padding: const EdgeInsets.fromLTRB(
                    AppSpacing.marginMobile, 24, AppSpacing.marginMobile, 40),
                decoration: const BoxDecoration(
                  color: AppColors.surfaceContainerLow,
                ),
                child: Stack(
                  children: [
                    Positioned(
                      top: -60,
                      right: -60,
                      child: _blurCircle(
                          AppColors.primaryContainer.withOpacity(0.25), 180),
                    ),
                    Positioned(
                      bottom: -60,
                      left: -60,
                      child: _blurCircle(
                          AppColors.secondaryContainer.withOpacity(0.20), 200),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Image.asset('assets/images/logo.png',
                                width: 32, height: 32),
                            const SizedBox(width: 8),
                            const Text('FitFuel',
                                style: TextStyle(
                                  fontFamily: 'Manrope',
                                  fontSize: 24,
                                  fontWeight: FontWeight.w800,
                                  color: AppColors.primary,
                                )),
                          ],
                        ),
                        const SizedBox(height: 28),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(AppRadius.lg),
                          child: Container(
                            height: 160,
                            width: double.infinity,
                            decoration: const BoxDecoration(
                              gradient: LinearGradient(
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                                colors: [
                                  AppColors.primaryContainer,
                                  AppColors.primary,
                                ],
                              ),
                            ),
                            child: Stack(
                              children: [
                                const Center(
                                  child: Icon(Icons.restaurant_menu,
                                      color: Colors.white, size: 56),
                                ),
                                Positioned(
                                  left: 16,
                                  right: 16,
                                  bottom: 12,
                                  child: Row(
                                    children: [
                                      const Icon(Icons.group,
                                          color: Colors.white, size: 18),
                                      const SizedBox(width: 6),
                                      Text('Join 50k+ members',
                                          style: AppTextStyles.labelSm
                                              .copyWith(color: Colors.white)),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 20),
                        Text('Fuel your journey.\nMaster your macros.',
                            style: AppTextStyles.headlineLgMobile),
                        const SizedBox(height: 10),
                        Text(
                          'Precision AI meets high-end nutrition. Sign in to access your personalized meal plans and performance insights.',
                          style: AppTextStyles.bodyMd
                              .copyWith(color: AppColors.onSurfaceVariant),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              // Form section
              Container(
                transform: Matrix4.translationValues(0, -24, 0),
                decoration: const BoxDecoration(
                  color: Color(0xFFFAF9F6),
                  borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                ),
                padding: const EdgeInsets.fromLTRB(
                    AppSpacing.marginMobile, 32, AppSpacing.marginMobile, 24),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text('Welcome back', style: AppTextStyles.headlineMd),
                      const SizedBox(height: 4),
                      Text('Enter your details to sign in.',
                          style: AppTextStyles.bodyMd
                              .copyWith(color: AppColors.onSurfaceVariant)),
                      const SizedBox(height: 24),
                      Text('Email Address', style: AppTextStyles.labelMd),
                      const SizedBox(height: 8),
                      TextFormField(
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        decoration: const InputDecoration(
                          hintText: 'you@example.com',
                          prefixIcon: Icon(Icons.mail_outline,
                              color: AppColors.outlineVariant),
                        ),
                        validator: (v) => (v == null || !v.contains('@'))
                            ? 'Enter a valid email'
                            : null,
                      ),
                      const SizedBox(height: 20),
                      Text('Password', style: AppTextStyles.labelMd),
                      const SizedBox(height: 8),
                      TextFormField(
                        controller: _passwordController,
                        obscureText: _obscure,
                        decoration: InputDecoration(
                          hintText: '••••••••',
                          prefixIcon: const Icon(Icons.lock_outline,
                              color: AppColors.outlineVariant),
                          suffixIcon: IconButton(
                            icon: Icon(
                              _obscure
                                  ? Icons.visibility_off_outlined
                                  : Icons.visibility_outlined,
                              color: AppColors.outlineVariant,
                            ),
                            onPressed: () =>
                                setState(() => _obscure = !_obscure),
                          ),
                        ),
                        validator: (v) => (v == null || v.length < 6)
                            ? 'Password must be at least 6 characters'
                            : null,
                      ),
                      if (_error != null) ...[
                        const SizedBox(height: 12),
                        Text(_error!,
                            style: const TextStyle(color: AppColors.error)),
                      ],
                      const SizedBox(height: 20),
                      ElevatedButton(
                        onPressed: _loading ? null : _submit,
                        style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.primaryContainer),
                        child: _loading
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2, color: Colors.white))
                            : const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text('Sign in'),
                                  SizedBox(width: 8),
                                  Icon(Icons.arrow_forward, size: 20),
                                ],
                              ),
                      ),
                      if (_wakingUp)
                        Padding(
                          padding: const EdgeInsets.only(top: 12),
                          child: Text(
                            'Waking up the server, this might take a minute...',
                            textAlign: TextAlign.center,
                            style: AppTextStyles.labelMd
                                .copyWith(color: AppColors.primary),
                          ),
                        ),
                      const SizedBox(height: 8),
                      const SizedBox(height: 28),
                      Center(
                        child: Wrap(
                          alignment: WrapAlignment.center,
                          children: [
                            Text("Don't have an account? ",
                                style: AppTextStyles.bodyMd.copyWith(
                                    color: AppColors.onSurfaceVariant)),
                            GestureDetector(
                              onTap: () => Navigator.of(context)
                                  .pushReplacementNamed('/register'),
                              child: Text('Register',
                                  style: AppTextStyles.labelMd.copyWith(
                                      color: AppColors.primary,
                                      fontWeight: FontWeight.w700)),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _blurCircle(Color color, double size) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(shape: BoxShape.circle, color: color),
    );
  }
}
