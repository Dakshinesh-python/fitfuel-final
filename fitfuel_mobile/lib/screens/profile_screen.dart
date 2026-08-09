import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

// ─── Section card ─────────────────────────────────────────────────────────────

class _SectionCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final List<Widget> children;
  const _SectionCard(
      {required this.title, required this.icon, required this.children});

  @override
  Widget build(BuildContext context) {
    return AppCard(
      radius: 18,
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: AppColors.primary, size: 20),
              const SizedBox(width: 8),
              Text(title,
                  style:
                      AppTextStyles.headlineMd.copyWith(fontSize: 16)),
            ],
          ),
          const SizedBox(height: 16),
          ...children,
        ],
      ),
    );
  }
}

// ─── Info row (label + value) ─────────────────────────────────────────────────

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        children: [
          Expanded(
              child: Text(label,
                  style: AppTextStyles.bodyMd
                      .copyWith(color: AppColors.onSurfaceVariant))),
          Text(value,
              style: AppTextStyles.bodyMd
                  .copyWith(fontWeight: FontWeight.w700)),
        ],
      ),
    );
  }
}

// ─── Toggle row ───────────────────────────────────────────────────────────────

class _ToggleRow extends StatelessWidget {
  final String label;
  final String sub;
  final bool value;
  final ValueChanged<bool> onChanged;
  const _ToggleRow(
      {required this.label,
      required this.sub,
      required this.value,
      required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: AppTextStyles.bodyMd),
                Text(sub,
                    style: AppTextStyles.labelSm
                        .copyWith(color: AppColors.onSurfaceVariant)),
              ],
            ),
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeTrackColor: AppColors.primary,
          ),
        ],
      ),
    );
  }
}

// ─── Password field ───────────────────────────────────────────────────────────

class _PasswordField extends StatefulWidget {
  final String label;
  final TextEditingController controller;
  const _PasswordField({required this.label, required this.controller});

  @override
  State<_PasswordField> createState() => _PasswordFieldState();
}

class _PasswordFieldState extends State<_PasswordField> {
  bool _obscure = true;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: widget.controller,
      obscureText: _obscure,
      decoration: InputDecoration(
        labelText: widget.label,
        suffixIcon: IconButton(
          icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility,
              size: 18),
          onPressed: () => setState(() => _obscure = !_obscure),
        ),
        border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppRadius.md)),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
    );
  }
}

// ─── Profile screen ───────────────────────────────────────────────────────────

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  // Data
  User? _user;
  HealthProfile? _profile;
  bool _loading = true;

  // Personal info
  late TextEditingController _nameCtrl;
  bool _savingName = false;

  // Security
  final _currentPwCtrl = TextEditingController();
  final _newPwCtrl = TextEditingController();
  final _confirmPwCtrl = TextEditingController();
  bool _savingPw = false;
  String? _pwMsg;
  bool _pwSuccess = false;

  // Preferences
  bool _notifPush = true;
  bool _notifMeals = true;
  bool _notifWeekly = false;

  static const _tabs = ['Personal', 'Health', 'Preferences', 'Security'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
    _nameCtrl = TextEditingController();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _loading = true);
    try {
      final results = await Future.wait([
        ApiService.instance.get('/api/auth/me'),
        ApiService.instance.get('/api/health-profile'),
      ], eagerError: false);

      if (mounted) {
        final userData = results[0];
        final hpData = results[1];
        setState(() {
          _user = User.fromJson(
              (userData['user'] ?? userData) as Map<String, dynamic>);
          _nameCtrl.text = _user?.name ?? '';
          if (hpData != null && hpData['profile'] != null) {
            _profile = HealthProfile.fromJson(
                hpData['profile'] as Map<String, dynamic>);
          }
        });
      }
    } catch (_) {
      // handle gracefully below
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _saveName() async {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) return;
    setState(() => _savingName = true);
    try {
      await ApiService.instance.put('/api/auth/profile', body: {'name': name});
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('Name updated successfully!'),
              backgroundColor: AppColors.primary),
        );
        _loadData();
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: AppColors.error),
        );
      }
    } finally {
      if (mounted) setState(() => _savingName = false);
    }
  }

  Future<void> _changePassword() async {
    final cur = _currentPwCtrl.text.trim();
    final nw = _newPwCtrl.text.trim();
    final conf = _confirmPwCtrl.text.trim();

    if (nw != conf) {
      setState(() {
        _pwMsg = 'New passwords do not match.';
        _pwSuccess = false;
      });
      return;
    }
    if (nw.length < 8) {
      setState(() {
        _pwMsg = 'Password must be at least 8 characters.';
        _pwSuccess = false;
      });
      return;
    }

    setState(() {
      _savingPw = true;
      _pwMsg = null;
    });
    try {
      await ApiService.instance.put('/api/auth/password', body: {
        'currentPassword': cur,
        'newPassword': nw,
      });
      _currentPwCtrl.clear();
      _newPwCtrl.clear();
      _confirmPwCtrl.clear();
      if (mounted) {
        setState(() {
          _pwMsg = 'Password changed successfully.';
          _pwSuccess = true;
        });
      }
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _pwMsg = e.message;
          _pwSuccess = false;
        });
      }
    } finally {
      if (mounted) setState(() => _savingPw = false);
    }
  }

  Future<void> _handleLogout() async {
    await AuthService.instance.logout();
    if (mounted) Navigator.of(context).pushReplacementNamed('/login');
  }

  // ─── Goal / activity labels ────────────────────────────────────────────────

  String _goalLabel(String g) => switch (g) {
        'WEIGHT_LOSS' => 'Weight Loss',
        'WEIGHT_GAIN' => 'Weight Gain',
        'MUSCLE_GAIN' => 'Muscle Gain',
        _ => 'Maintenance',
      };

  String _activityLabel(String a) => switch (a) {
        'SEDENTARY' => 'Sedentary',
        'LIGHT' => 'Light',
        'MODERATE' => 'Moderate',
        'ACTIVE' => 'Active',
        'VERY_ACTIVE' => 'Very Active',
        _ => a,
      };

  String _dietLabel(String d) => switch (d) {
        'VEGETARIAN' => 'Vegetarian',
        'NON_VEGETARIAN' => 'Non-Vegetarian',
        'VEGAN' => 'Vegan',
        _ => d,
      };

  // ─── Build ────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout_rounded),
            tooltip: 'Logout',
            onPressed: _handleLogout,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: _tabs.map((t) => Tab(text: t)).toList(),
          labelColor: AppColors.primary,
          unselectedLabelColor: AppColors.onSurfaceVariant,
          indicatorColor: AppColors.primary,
          labelStyle: AppTextStyles.labelMd
              .copyWith(fontWeight: FontWeight.w700),
          isScrollable: false,
        ),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SafeArea(
              top: false,
              child: TabBarView(
                controller: _tabController,
                children: [
                  _personalTab(),
                  _healthTab(),
                  _preferencesTab(),
                  _securityTab(),
                ],
              ),
            ),
      bottomNavigationBar: FitFuelBottomNav(
        currentIndex: 4,
        onTap: (i) {
          if (i == 0) Navigator.of(context).pushReplacementNamed('/dashboard');
          if (i == 1) Navigator.of(context).pushReplacementNamed('/recommendations');
          if (i == 2) Navigator.of(context).pushNamed('/chat');
          if (i == 3) Navigator.of(context).pushReplacementNamed('/progress');
        },
      ),
    );
  }

  // ─── Personal tab ─────────────────────────────────────────────────────────

  Widget _personalTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.marginMobile),
      child: Column(
        children: [
          // Avatar card
          AppCard(
            radius: 20,
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Container(
                  width: 64,
                  height: 64,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(colors: [
                      AppColors.primary,
                      Color(0xFF1B7A41),
                    ]),
                  ),
                  child:
                      const Icon(Icons.person_rounded, color: Colors.white, size: 32),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_user?.name ?? '—',
                          style: AppTextStyles.headlineMd
                              .copyWith(fontWeight: FontWeight.w700, fontSize: 18)),
                      Text(_user?.email ?? '—',
                          style: AppTextStyles.bodyMd
                              .copyWith(color: AppColors.onSurfaceVariant)),
                      const SizedBox(height: 6),
                      if (_profile != null)
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppColors.primaryContainer,
                            borderRadius:
                                BorderRadius.circular(AppRadius.full),
                          ),
                          child: Text(
                            _goalLabel(_profile!.fitnessGoal),
                            style: AppTextStyles.labelSm
                                .copyWith(color: AppColors.primary),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Edit name
          _SectionCard(
            title: 'Basic Information',
            icon: Icons.badge_rounded,
            children: [
              TextField(
                controller: _nameCtrl,
                decoration: InputDecoration(
                  labelText: 'Full Name',
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(AppRadius.md)),
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 14),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                enabled: false,
                decoration: InputDecoration(
                  labelText: 'Email Address',
                  hintText: _user?.email ?? '—',
                  helperText: 'Contact support to change your email.',
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(AppRadius.md)),
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 14),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _savingName ? null : _saveName,
                  style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: const StadiumBorder()),
                  child: _savingName
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2))
                      : const Text('Save Changes'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Danger zone
          AppCard(
            radius: 18,
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.warning_rounded, color: AppColors.error, size: 20),
                    const SizedBox(width: 8),
                    Text('Danger Zone',
                        style: AppTextStyles.headlineMd.copyWith(
                            fontSize: 16, color: AppColors.error)),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Deleting your account is permanent and cannot be undone.',
                  style: AppTextStyles.bodyMd
                      .copyWith(color: AppColors.onSurfaceVariant),
                ),
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () {},
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.error,
                    side: const BorderSide(color: AppColors.error),
                    shape: const StadiumBorder(),
                  ),
                  child: const Text('Delete Account'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ─── Health tab ───────────────────────────────────────────────────────────

  Widget _healthTab() {
    if (_profile == null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.monitor_heart_rounded,
                size: 56, color: AppColors.outline),
            const SizedBox(height: 16),
            const Text('No health profile found.'),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () =>
                  Navigator.of(context).pushNamed('/health-weight'),
              style: ElevatedButton.styleFrom(shape: const StadiumBorder()),
              child: const Text('Complete Assessment'),
            ),
          ],
        ),
      );
    }

    final p = _profile!;
    final rows = [
      ('Current Weight', '${p.currentWeightKg} kg'),
      ('Target Weight', '${p.targetWeightKg} kg'),
      ('Activity Level', _activityLabel(p.activityLevel)),
      ('Fitness Goal', _goalLabel(p.fitnessGoal)),
      ('Dietary Preference', _dietLabel(p.dietaryPreference)),
      ('Daily Budget', '₹${p.dailyBudget.toStringAsFixed(0)}'),
      if (p.bmi != null) ('BMI', p.bmi!.toStringAsFixed(1)),
      if (p.bmr != null) ('BMR', '${p.bmr!.round()} kcal'),
      if (p.tdee != null) ('TDEE', '${p.tdee!.round()} kcal'),
      if (p.proteinTargetG != null) ('Protein Target', '${p.proteinTargetG!.round()}g'),
      if (p.carbTargetG != null) ('Carb Target', '${p.carbTargetG}g'),
      if (p.fatTargetG != null) ('Fat Target', '${p.fatTargetG!.round()}g'),
    ];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.marginMobile),
      child: Column(
        children: [
          _SectionCard(
            title: 'Health Profile',
            icon: Icons.monitor_heart_rounded,
            children: [
              ...rows.map((r) => _InfoRow(label: r.$1, value: r.$2)),
              const SizedBox(height: 4),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () =>
                      Navigator.of(context).pushNamed('/health-weight'),
                  icon: const Icon(Icons.refresh_rounded, size: 18),
                  label: const Text('Retake Assessment'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: const StadiumBorder(),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ─── Preferences tab ──────────────────────────────────────────────────────

  Widget _preferencesTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.marginMobile),
      child: Column(
        children: [
          _SectionCard(
            title: 'Notifications',
            icon: Icons.notifications_rounded,
            children: [
              _ToggleRow(
                label: 'Push Notifications',
                sub: 'Receive push alerts on your device',
                value: _notifPush,
                onChanged: (v) => setState(() => _notifPush = v),
              ),
              _ToggleRow(
                label: 'Meal Reminders',
                sub: 'Get reminded at breakfast, lunch & dinner',
                value: _notifMeals,
                onChanged: (v) => setState(() => _notifMeals = v),
              ),
              _ToggleRow(
                label: 'Weekly Progress Report',
                sub: 'Receive a weekly nutrition summary',
                value: _notifWeekly,
                onChanged: (v) => setState(() => _notifWeekly = v),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _SectionCard(
            title: 'Diet Preferences',
            icon: Icons.restaurant_rounded,
            children: [
              Text(
                'Current preference: ',
                style: AppTextStyles.bodyMd
                    .copyWith(color: AppColors.onSurfaceVariant),
              ),
              const SizedBox(height: 4),
              Text(
                _profile != null
                    ? _dietLabel(_profile!.dietaryPreference)
                    : '—',
                style: AppTextStyles.bodyMd
                    .copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 12),
              Text(
                'To update your dietary preference, retake the health assessment.',
                style: AppTextStyles.labelSm
                    .copyWith(color: AppColors.onSurfaceVariant),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ─── Security tab ─────────────────────────────────────────────────────────

  Widget _securityTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.marginMobile),
      child: _SectionCard(
        title: 'Change Password',
        icon: Icons.lock_rounded,
        children: [
          _PasswordField(
              label: 'Current Password', controller: _currentPwCtrl),
          const SizedBox(height: 12),
          _PasswordField(label: 'New Password', controller: _newPwCtrl),
          const SizedBox(height: 12),
          _PasswordField(
              label: 'Confirm New Password', controller: _confirmPwCtrl),
          if (_pwMsg != null) ...[
            const SizedBox(height: 10),
            Text(
              _pwMsg!,
              style: AppTextStyles.bodyMd.copyWith(
                  color: _pwSuccess ? AppColors.primary : AppColors.error),
            ),
          ],
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _savingPw ? null : _changePassword,
              style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: const StadiumBorder()),
              child: _savingPw
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2))
                  : const Text('Update Password'),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    _nameCtrl.dispose();
    _currentPwCtrl.dispose();
    _newPwCtrl.dispose();
    _confirmPwCtrl.dispose();
    super.dispose();
  }
}
