import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/features/upload/providers/document_provider.dart';

class DocumentChatScreen extends StatefulWidget {
  final String documentId;
  final String documentName;

  const DocumentChatScreen({
    super.key,
    required this.documentId,
    required this.documentName,
  });

  @override
  State<DocumentChatScreen> createState() => _DocumentChatScreenState();
}

class _DocumentChatScreenState extends State<DocumentChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  final List<String> _quickQuestions = [
    'Summarize this document',
    'What are the main risks?',
    'What is the termination clause?',
    'Who are the involved parties?',
    'What are the payment terms?',
    'Find confidential clauses',
  ];

  @override
  void initState() {
    super.initState();
    // Load existing chat history
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DocumentProvider>().loadChatHistory(widget.documentId);
    });
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage([String? customMessage]) async {
    final message = customMessage ?? _messageController.text.trim();
    if (message.isEmpty) return;

    _messageController.clear();
    final provider = context.read<DocumentProvider>();
    await provider.sendChatMessage(widget.documentId, message);

    // Scroll to bottom
    if (_scrollController.hasClients) {
      await Future.delayed(const Duration(milliseconds: 100));
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<DocumentProvider>();
    final messages = provider.chatMessages;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.cardDark,
        elevation: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('AI Legal Assistant',
                style: GoogleFonts.inter(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary)),
            Text(widget.documentName,
                style: GoogleFonts.inter(
                    fontSize: 12, color: AppColors.textSecondary),
                overflow: TextOverflow.ellipsis),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.delete_outline, color: AppColors.textSecondary),
            onPressed: () {
              provider.clearChat();
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Chat messages
          Expanded(
            child: messages.isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    itemCount: messages.length + (provider.isChatting ? 1 : 0),
                    itemBuilder: (context, index) {
                      if (index == messages.length && provider.isChatting) {
                        return _buildTypingIndicator();
                      }
                      return _buildMessageBubble(messages[index]);
                    },
                  ),
          ),

          // Quick questions (show only when no messages)
          if (messages.isEmpty)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _quickQuestions
                    .map((q) => GestureDetector(
                          onTap: () => _sendMessage(q),
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 14, vertical: 8),
                            decoration: BoxDecoration(
                              color: AppColors.cardDark,
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(color: AppColors.border),
                            ),
                            child: Text(q,
                                style: GoogleFonts.inter(
                                    fontSize: 12,
                                    color: AppColors.gold,
                                    fontWeight: FontWeight.w500)),
                          ),
                        ))
                    .toList(),
              ),
            ),

          // Input bar
          Container(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
            decoration: BoxDecoration(
              color: AppColors.cardDark,
              border: Border(top: BorderSide(color: AppColors.border)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    decoration: BoxDecoration(
                      color: AppColors.background,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: TextField(
                      controller: _messageController,
                      style: GoogleFonts.inter(
                          fontSize: 14, color: AppColors.textPrimary),
                      decoration: InputDecoration(
                        hintText: 'Ask about this document...',
                        hintStyle: GoogleFonts.inter(
                            fontSize: 14, color: AppColors.textHint),
                        border: InputBorder.none,
                        contentPadding:
                            const EdgeInsets.symmetric(vertical: 12),
                      ),
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _sendMessage(),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: provider.isChatting ? null : () => _sendMessage(),
                  child: Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: provider.isChatting
                          ? AppColors.gold.withValues(alpha: 0.3)
                          : AppColors.gold,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.send, color: AppColors.navy, size: 20),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: AppColors.goldGlow,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.auto_awesome, size: 48, color: AppColors.gold),
          ).animate().scale(curve: Curves.elasticOut),
          const SizedBox(height: 24),
          Text('Ask me anything',
              style: GoogleFonts.inter(
                  fontSize: 22,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary)),
          const SizedBox(height: 8),
          Text('I can help you understand\nthis legal document',
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(
                  fontSize: 14, color: AppColors.textSecondary, height: 1.5)),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(Map<String, dynamic> message) {
    final isUser = message['role'] == 'user';

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: AppColors.goldGlow,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.auto_awesome,
                  size: 16, color: AppColors.gold),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: isUser
                    ? AppColors.gold.withOpacity(0.15)
                    : AppColors.cardDark,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(isUser ? 16 : 4),
                  bottomRight: Radius.circular(isUser ? 4 : 16),
                ),
                border: Border.all(
                  color: isUser
                      ? AppColors.gold.withOpacity(0.3)
                      : AppColors.border,
                ),
              ),
              child: SelectableText(
                message['content'] ?? '',
                style: GoogleFonts.inter(
                  fontSize: 13,
                  color: AppColors.textPrimary,
                  height: 1.5,
                ),
              ),
            ),
          ),
          if (isUser) const SizedBox(width: 8),
        ],
      ),
    ).animate().fadeIn(duration: 200.ms).slideX(
          begin: isUser ? 0.1 : -0.1,
          end: 0,
          duration: 200.ms,
        );
  }

  Widget _buildTypingIndicator() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: AppColors.goldGlow,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.auto_awesome, size: 16, color: AppColors.gold),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: AppColors.cardDark,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(16),
                topRight: Radius.circular(16),
                bottomRight: Radius.circular(16),
                bottomLeft: Radius.circular(4),
              ),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _dot(0),
                const SizedBox(width: 4),
                _dot(200),
                const SizedBox(width: 4),
                _dot(400),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _dot(int delayMs) {
    return Container(
      width: 8,
      height: 8,
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.6),
        shape: BoxShape.circle,
      ),
    )
        .animate(onPlay: (c) => c.repeat(reverse: true))
        .scaleXY(begin: 0.5, end: 1.0, delay: Duration(milliseconds: delayMs))
        .fadeIn();
  }
}
