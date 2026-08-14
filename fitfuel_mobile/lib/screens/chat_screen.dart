import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/app_widgets.dart';

// ─── Chat message model ───────────────────────────────────────────────────────

class _ChatMessage {
  final String id;
  final bool isUser;
  final String text;
  final DateTime time;

  _ChatMessage({
    required this.id,
    required this.isUser,
    required this.text,
    required this.time,
  });
}

// ─── Quick replies ────────────────────────────────────────────────────────────

const _quickReplies = [
  'What should I eat after a workout?',
  'Suggest a high-protein breakfast',
  'How can I reduce carbs?',
  'Best snacks for weight loss?',
  'Show protein shake options',
  'What is a good low-calorie dinner?',
];

// ─── Chat screen ──────────────────────────────────────────────────────────────

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  static final List<_ChatMessage> _messages = [];
  bool _sending = false;
  HealthProfile? _profile;
  List<String> _shownQuickReplies = _quickReplies.take(3).toList();

  @override
  void initState() {
    super.initState();
    if (_messages.isEmpty) {
      _addAIMessage(
          "Hi there! I'm your FitFuel AI nutritionist 🥗\nHow can I help you adjust your meal plan today?");
    }
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final data = await ApiService.instance.get('/api/health-profile');
      if (mounted) {
        setState(() {
          _profile =
              HealthProfile.fromJson(data['profile'] as Map<String, dynamic>);
        });
      }
    } catch (_) {
      // non-fatal — chat still works without profile context
    }
  }

  void _addAIMessage(String text) {
    setState(() {
      _messages.add(_ChatMessage(
        id: DateTime.now().microsecondsSinceEpoch.toString(),
        isUser: false,
        text: text,
        time: DateTime.now(),
      ));
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _send(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || _sending) return;

    _controller.clear();
    setState(() {
      _messages.add(_ChatMessage(
        id: DateTime.now().microsecondsSinceEpoch.toString(),
        isUser: true,
        text: trimmed,
        time: DateTime.now(),
      ));
      _sending = true;
      _shownQuickReplies = [];
    });
    _scrollToBottom();

    try {
      final data = await ApiService.instance
          .post('/api/chat', body: {'message': trimmed});
      final reply = data['reply'] as String? ??
          "I couldn't process that. Please try again.";
      _addAIMessage(reply);
      // Rotate quick replies
      final start = (_messages.length * 2) % (_quickReplies.length - 3);
      setState(() {
        _shownQuickReplies = _quickReplies.skip(start).take(3).toList();
      });
    } on ApiException catch (e) {
      _addAIMessage("Sorry, I hit an error: ${e.message}");
    } catch (_) {
      _addAIMessage(
          "I'm having trouble right now. Please try again in a moment.");
    } finally {
      if (mounted) setState(() => _sending = false);
      _scrollToBottom();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                  colors: [AppColors.primary, Color(0xFF1B7A41)],
                ),
              ),
              child: const Icon(Icons.smart_toy_rounded,
                  color: Colors.white, size: 20),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('FitFuel AI', style: TextStyle(fontSize: 16)),
                Text('Nutrition Coach',
                    style: TextStyle(
                        fontSize: 11,
                        color: AppColors.onSurfaceVariant,
                        fontWeight: FontWeight.w400)),
              ],
            ),
          ],
        ),
        actions: [
          // Show macro target context
          if (_profile != null)
            Padding(
              padding: const EdgeInsets.only(right: 12),
              child: Chip(
                label: Text(
                  _profile!.fitnessGoal.replaceAll('_', ' '),
                  style: AppTextStyles.labelSm
                      .copyWith(color: AppColors.primary, fontSize: 10),
                ),
                backgroundColor: AppColors.primaryContainer,
                side: BorderSide.none,
                padding: EdgeInsets.zero,
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
            ),
        ],
      ),
      body: SafeArea(
        top: false,
        child: Column(
          children: [
            // Messages list
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.marginMobile, vertical: 12),
                itemCount: _messages.length + (_sending ? 1 : 0),
                itemBuilder: (_, i) {
                  if (i == _messages.length) {
                    return _TypingBubble();
                  }
                  return _MessageBubble(msg: _messages[i]);
                },
              ),
            ),

            // Quick replies
            if (_shownQuickReplies.isNotEmpty && !_sending)
              SizedBox(
                height: 44,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: _shownQuickReplies.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemBuilder: (_, i) => GestureDetector(
                    onTap: () => _send(_shownQuickReplies[i]),
                    child: Container(
                      alignment: Alignment.center,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 8),
                      decoration: BoxDecoration(
                        border: Border.all(
                            color: AppColors.outlineVariant, width: 1),
                        borderRadius: BorderRadius.circular(AppRadius.full),
                        color: Colors.white,
                      ),
                      child: Text(_shownQuickReplies[i],
                          style: AppTextStyles.labelSm
                              .copyWith(color: AppColors.onSurface)),
                    ),
                  ),
                ),
              ),

            const SizedBox(height: 8),

            // Input bar
            Padding(
              padding: const EdgeInsets.only(
                left: 12,
                right: 12,
                bottom: 8,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      enabled: !_sending,
                      textInputAction: TextInputAction.send,
                      onSubmitted: _send,
                      decoration: InputDecoration(
                        hintText: 'Ask your nutritionist…',
                        hintStyle: AppTextStyles.bodyMd
                            .copyWith(color: AppColors.onSurfaceVariant),
                        filled: true,
                        fillColor: AppColors.surfaceContainerHigh,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(AppRadius.full),
                          borderSide: BorderSide.none,
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: 18, vertical: 12),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  // Send button
                  GestureDetector(
                    onTap: _sending ? null : () => _send(_controller.text),
                    child: Container(
                      width: 48,
                      height: 48,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          colors: [AppColors.primary, Color(0xFF1B7A41)],
                        ),
                      ),
                      child: _sending
                          ? const Padding(
                              padding: EdgeInsets.all(14),
                              child: CircularProgressIndicator(
                                  color: Colors.white, strokeWidth: 2),
                            )
                          : const Icon(Icons.send_rounded,
                              color: Colors.white, size: 22),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: FitFuelBottomNav(
        currentIndex: 2,
        onTap: (i) {
          if (i == 0) Navigator.of(context).pushReplacementNamed('/dashboard');
          if (i == 1)
            Navigator.of(context).pushReplacementNamed('/recommendations');
          if (i == 3) Navigator.of(context).pushReplacementNamed('/progress');
          if (i == 4) Navigator.of(context).pushReplacementNamed('/profile');
        },
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}

// ─── Message bubble ───────────────────────────────────────────────────────────

class _MessageBubble extends StatelessWidget {
  final _ChatMessage msg;
  const _MessageBubble({required this.msg});

  @override
  Widget build(BuildContext context) {
    final isUser = msg.isUser;
    final timeStr =
        '${msg.time.hour.toString().padLeft(2, '0')}:${msg.time.minute.toString().padLeft(2, '0')}';

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              width: 32,
              height: 32,
              decoration: const BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(
                    colors: [AppColors.primary, Color(0xFF1B7A41)]),
              ),
              child: const Icon(Icons.smart_toy_rounded,
                  color: Colors.white, size: 18),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Column(
              crossAxisAlignment:
                  isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: isUser ? AppColors.primary : Colors.white,
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(18),
                      topRight: const Radius.circular(18),
                      bottomLeft: Radius.circular(isUser ? 18 : 4),
                      bottomRight: Radius.circular(isUser ? 4 : 18),
                    ),
                    boxShadow: kCardShadowLevel1,
                  ),
                  child: Text(
                    msg.text,
                    style: AppTextStyles.bodyMd.copyWith(
                      color: isUser ? Colors.white : AppColors.onSurface,
                      height: 1.4,
                    ),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  timeStr,
                  style: AppTextStyles.labelSm.copyWith(
                      color: AppColors.onSurfaceVariant, fontSize: 10),
                ),
              ],
            ),
          ),
          if (isUser) ...[
            const SizedBox(width: 8),
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.secondaryContainer,
              ),
              child: const Icon(Icons.person_rounded,
                  color: AppColors.onSurface, size: 18),
            ),
          ],
        ],
      ),
    );
  }
}

// ─── Typing indicator ─────────────────────────────────────────────────────────

class _TypingBubble extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                  colors: [AppColors.primary, Color(0xFF1B7A41)]),
            ),
            child: const Icon(Icons.smart_toy_rounded,
                color: Colors.white, size: 18),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(18),
                topRight: Radius.circular(18),
                bottomRight: Radius.circular(18),
                bottomLeft: Radius.circular(4),
              ),
              boxShadow: kCardShadowLevel1,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: List.generate(
                3,
                (i) => _Dot(delay: Duration(milliseconds: i * 150)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Dot extends StatefulWidget {
  final Duration delay;
  const _Dot({required this.delay});

  @override
  State<_Dot> createState() => _DotState();
}

class _DotState extends State<_Dot> with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;
  late Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 600))
      ..repeat(reverse: true);
    _anim = Tween(begin: 0.0, end: -6.0).animate(
      CurvedAnimation(
          parent: _ctrl, curve: Interval(0, 1, curve: Curves.easeInOut)),
    );
    Future.delayed(widget.delay, () {
      if (mounted) _ctrl.forward();
    });
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _anim,
      builder: (_, __) => Transform.translate(
        offset: Offset(0, _anim.value),
        child: Container(
          width: 8,
          height: 8,
          margin: const EdgeInsets.symmetric(horizontal: 3),
          decoration: const BoxDecoration(
            shape: BoxShape.circle,
            color: AppColors.onSurfaceVariant,
          ),
        ),
      ),
    );
  }
}
