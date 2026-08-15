import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../widgets/app_widgets.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _ageController = TextEditingController();
  final _heightController = TextEditingController();
  final _weightController = TextEditingController();
  String _gender = 'female';
  bool _loading = false;
  bool _wakingUp = false;
  Timer? _wakeTimer;
  String? _error;

  @override
  void dispose() {
    _wakeTimer?.cancel();
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _ageController.dispose();
    _heightController.dispose();
    _weightController.dispose();
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
      await AuthService.instance.register(
        name: _nameController.text.trim(),
        email: _emailController.text.trim(),
        password: _passwordController.text,
        age: int.tryParse(_ageController.text),
        gender: _gender.toUpperCase(),
        heightCm: double.tryParse(_heightController.text),
        weightKg: double.tryParse(_weightController.text),
      );
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed(
        '/health-weight',
        arguments: {'currentWeightKg': double.tryParse(_weightController.text)},
      );
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

  InputDecoration _dec(String hint) => InputDecoration(hintText: hint);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.marginMobile, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Column(
                children: [
                  Text('FitFuel',
                      textAlign: TextAlign.center,
                      style: AppTextStyles.headlineLgMobile
                          .copyWith(color: AppColors.primary)),
                  const SizedBox(height: 4),
                  Text('Create your health profile',
                      textAlign: TextAlign.center,
                      style: AppTextStyles.bodyMd
                          .copyWith(color: AppColors.onSurfaceVariant)),
                ],
              ),
              const SizedBox(height: 24),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppColors.surfaceContainerLowest.withOpacity(0.9),
                  borderRadius: BorderRadius.circular(AppRadius.lg),
                  boxShadow: kCardShadowLevel1,
                ),
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Step 1 of 3',
                              style: AppTextStyles.labelSm
                                  .copyWith(color: AppColors.primary)),
                          Text('Basics',
                              style: AppTextStyles.labelSm
                                  .copyWith(color: AppColors.onSurfaceVariant)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      const StepProgressBar(currentStep: 1, totalSteps: 3),
                      const SizedBox(height: 24),
                      Text('Full Name', style: AppTextStyles.labelMd),
                      const SizedBox(height: 6),
                      TextFormField(
                        key: const ValueKey('register_name_field'),
                        controller: _nameController,
                        decoration: _dec('Jane Doe'),
                        validator: (v) =>
                            (v == null || v.isEmpty) ? 'Required' : null,
                      ),
                      const SizedBox(height: 16),
                      Text('Email Address', style: AppTextStyles.labelMd),
                      const SizedBox(height: 6),
                      TextFormField(
                        key: const ValueKey('register_email_field'),
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        decoration: _dec('jane@example.com'),
                        validator: (v) => (v == null || !v.contains('@'))
                            ? 'Enter a valid email'
                            : null,
                      ),
                      const SizedBox(height: 16),
                      Text('Password', style: AppTextStyles.labelMd),
                      const SizedBox(height: 6),
                      TextFormField(
                        key: const ValueKey('register_password_field'),
                        controller: _passwordController,
                        obscureText: true,
                        decoration: _dec('••••••••'),
                        validator: (v) => (v == null || v.length < 6)
                            ? 'Min 6 characters'
                            : null,
                      ),
                      const SizedBox(height: 20),
                      const Divider(color: AppColors.surfaceContainerHighest),
                      const SizedBox(height: 20),
                      Text('Age', style: AppTextStyles.labelMd),
                      const SizedBox(height: 6),
                      TextFormField(
                        key: const ValueKey('register_age_field'),
                        controller: _ageController,
                        keyboardType: TextInputType.number,
                        decoration: _dec('Years'),
                        validator: (v) =>
                            (v == null || v.isEmpty) ? 'Required' : null,
                      ),
                      const SizedBox(height: 16),
                      Text('Gender', style: AppTextStyles.labelMd),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: AppColors.surfaceContainerHighest,
                          borderRadius: BorderRadius.circular(AppRadius.dflt),
                        ),
                        child: Row(
                          children: ['male', 'female', 'other'].map((g) {
                            final selected = _gender == g;
                            return Expanded(
                              child: GestureDetector(
                                key: ValueKey('register_gender_option_$g'),
                                onTap: () => setState(() => _gender = g),
                                child: Container(
                                  padding:
                                      const EdgeInsets.symmetric(vertical: 10),
                                  decoration: BoxDecoration(
                                    color: selected
                                        ? Colors.white
                                        : Colors.transparent,
                                    borderRadius:
                                        BorderRadius.circular(AppRadius.sm),
                                    boxShadow:
                                        selected ? kCardShadowLevel1 : null,
                                  ),
                                  alignment: Alignment.center,
                                  child: Text(
                                    g[0].toUpperCase() + g.substring(1),
                                    style: AppTextStyles.labelMd.copyWith(
                                        color: AppColors.onSurfaceVariant),
                                  ),
                                ),
                              ),
                            );
                          }).toList(),
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Height (cm)',
                                    style: AppTextStyles.labelMd),
                                const SizedBox(height: 6),
                                TextFormField(
                                  key: const ValueKey('register_height_field'),
                                  controller: _heightController,
                                  keyboardType: TextInputType.number,
                                  decoration: _dec('170'),
                                  validator: (v) => (v == null || v.isEmpty)
                                      ? 'Required'
                                      : null,
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Weight (kg)',
                                    style: AppTextStyles.labelMd),
                                const SizedBox(height: 6),
                                TextFormField(
                                  key: const ValueKey('register_weight_field'),
                                  controller: _weightController,
                                  keyboardType: TextInputType.number,
                                  decoration: _dec('65'),
                                  validator: (v) => (v == null || v.isEmpty)
                                      ? 'Required'
                                      : null,
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      if (_error != null) ...[
                        Text(_error!,
                            key: const ValueKey('register_error_text'),
                            style: const TextStyle(color: AppColors.error)),
                        const SizedBox(height: 12),
                      ],
                      ElevatedButton(
                        key: const ValueKey('register_submit_button'),
                        onPressed: _loading ? null : _submit,
                        child: _loading
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2, color: Colors.white))
                            : const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text('Continue'),
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
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),
              Center(
                child: Wrap(
                  alignment: WrapAlignment.center,
                  children: [
                    Text('Already have an account? ',
                        style: AppTextStyles.bodyMd
                            .copyWith(color: AppColors.onSurfaceVariant)),
                    GestureDetector(
                      key: const ValueKey('register_login_link'),
                      onTap: () =>
                          Navigator.of(context).pushReplacementNamed('/login'),
                      child: Text('Log in',
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
    );
  }
}
