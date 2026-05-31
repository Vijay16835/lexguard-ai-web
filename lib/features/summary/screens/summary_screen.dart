import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/features/summary/providers/summary_provider.dart';
import 'package:lexguard_ai/features/home/providers/home_provider.dart';
import 'package:lexguard_ai/features/language/providers/language_provider.dart';
import 'package:lexguard_ai/models/document_model.dart';
import 'package:lexguard_ai/models/summary_model.dart';
import 'package:lexguard_ai/services/tts_service.dart';
import 'package:lexguard_ai/features/profile/providers/profile_provider.dart';

class SummaryScreen extends StatefulWidget {
  const SummaryScreen({super.key});

  @override
  State<SummaryScreen> createState() => _SummaryScreenState();
}

class _SummaryScreenState extends State<SummaryScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initSummary();
    });
  }

  void _initSummary() {
    final recentDocs = context.read<HomeProvider>().recentDocuments;
    if (recentDocs.isNotEmpty) {
      context.read<SummaryProvider>().generateSummary(recentDocs.first);
    }
  }

  @override
  Widget build(BuildContext context) {
    final summaryProvider = context.watch<SummaryProvider>();
    final recentDocs = context.watch<HomeProvider>().recentDocuments;
    final tts = context.watch<TtsService>();
    final langProvider = context.watch<LanguageProvider>();
    context.watch<ProfileProvider>();

    // Text that will be read aloud — available once summary loads
    final summaryText = summaryProvider.summary?.shortSummary ?? '';

    // Sync SummaryProvider language with LanguageProvider
    if (summaryProvider.selectedLanguage != langProvider.selectedLanguage) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        summaryProvider.translateSummary(langProvider.selectedLanguage).catchError((_) {});
      });
    }

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        centerTitle: true,
        title: Text(
          'AI Document Summary',
          style: GoogleFonts.inter(
            color: AppColors.textPrimary,
            fontSize: 18,
            fontWeight: FontWeight.w700,
          ),
        ),
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios_new, color: AppColors.textPrimary, size: 20),
          onPressed: () {
            tts.stop(); // stop TTS when leaving the screen
            Navigator.pop(context);
          },
        ),
        actions: [
          if (summaryText.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(right: 8),
              child: _AppBarTtsButton(
                summaryText: summaryText,
                language: langProvider.selectedLanguage,
                tts: tts,
              ),
            ),
        ],
      ),
      body: _buildBody(summaryProvider, recentDocs.isNotEmpty ? recentDocs.first : null),
    );
  }

  Widget _buildBody(SummaryProvider provider, DocumentModel? document) {
    if (document == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.folder_off_outlined, color: AppColors.textSecondary, size: 64),
            const SizedBox(height: 16),
            Text('No Documents Found', style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
            const SizedBox(height: 8),
            Text('Upload a document first to generate a summary.', style: GoogleFonts.inter(color: AppColors.textSecondary)),
          ],
        ),
      );
    }

    if (provider.state == SummaryState.idle || provider.state == SummaryState.processing) {
      return _buildLoadingState(document);
    } else if (provider.state == SummaryState.error) {
      return _buildErrorState(provider.errorMessage ?? 'An unknown error occurred.', document);
    } else if (provider.state == SummaryState.success && provider.summary != null) {
      return _buildSuccessState(provider.summary!, document, provider);
    }

    return const SizedBox();
  }

  Widget _buildLoadingState(DocumentModel document) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: AppColors.gold.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: const CircularProgressIndicator(color: AppColors.gold, strokeWidth: 3),
          ).animate(onPlay: (controller) => controller.repeat()).shimmer(duration: 2000.ms),
          const SizedBox(height: 32),
          Text('Analyzing Document...', style: GoogleFonts.inter(fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.textPrimary)).animate().fadeIn(duration: 500.ms),
          const SizedBox(height: 12),
          Text(document.name, style: GoogleFonts.inter(fontSize: 14, color: AppColors.textSecondary)).animate().fadeIn(delay: 200.ms),
          const SizedBox(height: 8),
          Text('Extracting key clauses and recommendations', style: GoogleFonts.inter(fontSize: 12, color: AppColors.gold)).animate().fadeIn(delay: 400.ms),
        ],
      ),
    );
  }

  Widget _buildErrorState(String error, DocumentModel document) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: AppColors.error, size: 64),
            const SizedBox(height: 24),
            Text('Failed to Generate Summary', style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
            const SizedBox(height: 12),
            Text(error, textAlign: TextAlign.center, style: GoogleFonts.inter(fontSize: 14, color: AppColors.textSecondary)),
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () => context.read<SummaryProvider>().generateSummary(document),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.gold,
                foregroundColor: AppColors.navy,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              icon: const Icon(Icons.refresh),
              label: Text('Try Again', style: GoogleFonts.inter(fontWeight: FontWeight.w600)),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSuccessState(SummaryModel summary, DocumentModel document, SummaryProvider provider) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Document Header
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [Color(0xFF1E3A6E), Color(0xFF0D1F3C)]),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(color: AppColors.gold.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
                  child: const Icon(Icons.description_outlined, color: AppColors.gold, size: 28),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(document.name, style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.textPrimary), maxLines: 1, overflow: TextOverflow.ellipsis),
                      const SizedBox(height: 4),
                      Text('Generated ${summary.generatedAt.toLocal().toString().split('.')[0]}', style: GoogleFonts.inter(fontSize: 12, color: AppColors.textSecondary)),
                    ],
                  ),
                ),
              ],
            ),
          ).animate().fadeIn().slideY(begin: 0.1, end: 0),
          
          const SizedBox(height: 16),

          // Translation Control Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.cardDark,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.translate_rounded, color: AppColors.gold, size: 18),
                    const SizedBox(width: 8),
                    Text('Summary Language', style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
                  ],
                ),
                DropdownButton<String>(
                  value: context.watch<LanguageProvider>().selectedLanguage,
                  dropdownColor: AppColors.cardDark,
                  style: GoogleFonts.inter(color: AppColors.textPrimary, fontSize: 13, fontWeight: FontWeight.w600),
                  underline: const SizedBox(),
                  icon: const Icon(Icons.keyboard_arrow_down, color: AppColors.gold),
                  items: kSupportedLanguages.map((lang) {
                    return DropdownMenuItem<String>(
                      value: lang,
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(kLanguageFlags[lang] ?? '🌐', style: const TextStyle(fontSize: 14)),
                          const SizedBox(width: 6),
                          Text(lang),
                        ],
                      ),
                    );
                  }).toList(),
                  onChanged: (val) {
                    if (val != null) {
                      final messenger = ScaffoldMessenger.of(context);
                      context.read<LanguageProvider>().setLanguage(val);
                      context.read<SummaryProvider>().translateSummary(val).catchError((_) {
                        messenger.showSnackBar(
                          SnackBar(
                            content: Text('Translation to $val failed. Showing English summary.'),
                            backgroundColor: AppColors.warning,
                            duration: const Duration(seconds: 3),
                          ),
                        );
                      });
                    }
                  },
                ),
              ],
            ),
          ),

          const SizedBox(height: 24),
          
          _SectionCard(
            title: 'Executive Summary',
            icon: Icons.summarize_outlined,
            color: AppColors.gold,
            content: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(summary.shortSummary, style: GoogleFonts.inter(fontSize: 14, color: AppColors.textSecondary, height: 1.5)),
                const SizedBox(height: 16),
                Divider(color: AppColors.border, height: 1),
                const SizedBox(height: 12),
                _TtsPlaybackControls(textToSpeak: summary.shortSummary),
              ],
            ),
            delay: 100,
          ),
          
          const SizedBox(height: 16),
          _ListSection(title: 'Key Clauses', icon: Icons.gavel_rounded, color: const Color(0xFF3498DB), items: summary.keyClauses, delay: 150),
          
          const SizedBox(height: 16),
          _ListSection(title: 'Important Dates', icon: Icons.calendar_today_outlined, color: const Color(0xFF9B59B6), items: summary.importantDates, delay: 200),
          
          const SizedBox(height: 16),
          _ListSection(title: 'Parties Involved', icon: Icons.people_outline, color: const Color(0xFFE67E22), items: summary.partiesInvolved, delay: 250),
          
          const SizedBox(height: 16),
          _ListSection(title: 'Obligations', icon: Icons.assignment_outlined, color: AppColors.info, items: summary.obligations, delay: 300),
          
          const SizedBox(height: 16),
          _ListSection(title: 'Recommendations', icon: Icons.lightbulb_outline, color: AppColors.success, items: summary.recommendations, delay: 350),
          
          const SizedBox(height: 40),
        ],
      ),
    );
  }
}

// ── AppBar quick-access speaker button ─────────────────────────────────────
class _AppBarTtsButton extends StatelessWidget {
  final String summaryText;
  final String language;
  final TtsService tts;

  const _AppBarTtsButton({
    required this.summaryText,
    required this.language,
    required this.tts,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 250),
      child: tts.isPlaying
          ? IconButton(
              key: const ValueKey('stop'),
              tooltip: 'Stop reading',
              icon: const Icon(Icons.stop_circle_outlined, color: Colors.redAccent, size: 26),
              onPressed: tts.stop,
            )
          : IconButton(
              key: const ValueKey('speak'),
              tooltip: tts.isPaused ? 'Resume reading' : 'Read summary aloud',
              icon: Icon(
                tts.isPaused ? Icons.play_circle_outline : Icons.volume_up_rounded,
                color: AppColors.gold,
                size: 26,
              ),
              onPressed: tts.isPaused
                  ? tts.resume
                  : () => tts.speak(summaryText, languageCode: language),
            ),
    );
  }
}

// ── In-card TTS playback controls ──────────────────────────────────────────
class _TtsPlaybackControls extends StatelessWidget {
  final String textToSpeak;

  const _TtsPlaybackControls({required this.textToSpeak});

  @override
  Widget build(BuildContext context) {
    final tts = context.watch<TtsService>();
    // Read language from shared LanguageProvider
    final language = context.watch<LanguageProvider>().selectedLanguage;

    // Tri-state status label
    final String statusLabel;
    final Color statusColor;
    if (tts.isPlaying) {
      statusLabel = 'Speaking AI Summary...';
      statusColor = AppColors.gold;
    } else if (tts.isPaused) {
      statusLabel = 'Paused — tap ▶ to resume';
      statusColor = AppColors.textSecondary;
    } else {
      statusLabel = 'Read Aloud Summary';
      statusColor = AppColors.textHint;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Status row
        Row(
          children: [
            Icon(Icons.volume_up_rounded, size: 16, color: statusColor),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                statusLabel,
                style: GoogleFonts.inter(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: statusColor,
                ),
              ),
            ),
            // Blinking dot only while playing
            if (tts.isPlaying)
              Container(
                width: 8, height: 8,
                decoration: const BoxDecoration(color: Colors.redAccent, shape: BoxShape.circle),
              ).animate(onPlay: (c) => c.repeat())
                .fadeIn(duration: 500.ms)
                .fadeOut(duration: 500.ms),
          ],
        ),
        const SizedBox(height: 8),
        // Control buttons
        Row(
          children: [
            // Play / Resume button
            IconButton(
              tooltip: tts.isPaused ? 'Resume' : 'Play',
              icon: Icon(
                tts.isPaused ? Icons.play_arrow_rounded : Icons.volume_up_rounded,
                color: tts.isPlaying ? AppColors.textHint : AppColors.gold,
                size: 28,
              ),
              onPressed: tts.isPlaying
                  ? null
                  : tts.isPaused
                      ? tts.resume
                      : () => tts.speak(textToSpeak, languageCode: language),
            ),
            // Pause button
            IconButton(
              tooltip: 'Pause',
              icon: Icon(
                Icons.pause_rounded,
                color: tts.isPlaying ? AppColors.gold : AppColors.textHint,
                size: 28,
              ),
              onPressed: tts.isPlaying ? tts.pause : null,
            ),
            // Stop button
            IconButton(
              tooltip: 'Stop',
              icon: Icon(
                Icons.stop_rounded,
                color: (tts.isPlaying || tts.isPaused) ? Colors.redAccent : AppColors.textHint,
                size: 28,
              ),
              onPressed: (tts.isPlaying || tts.isPaused) ? tts.stop : null,
            ),
            const Spacer(),
            Text(
              '${tts.speechRate.toStringAsFixed(1)}x',
              style: GoogleFonts.inter(
                fontSize: 12,
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        // Speed slider
        Row(
          children: [
            Icon(Icons.speed, size: 16, color: AppColors.textHint),
            Expanded(
              child: Slider(
                value: tts.speechRate,
                min: 0.3,
                max: 1.5,
                divisions: 6,
                activeColor: AppColors.gold,
                inactiveColor: AppColors.border,
                onChanged: tts.setRate,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _SectionCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;
  final Widget content;
  final int delay;

  const _SectionCard({required this.title, required this.icon, required this.color, required this.content, required this.delay});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.cardDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 20),
              const SizedBox(width: 10),
              Text(title, style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
            ],
          ),
          const SizedBox(height: 16),
          content,
        ],
      ),
    ).animate(delay: Duration(milliseconds: delay)).fadeIn().slideY(begin: 0.1, end: 0);
  }
}

class _ListSection extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;
  final List<String> items;
  final int delay;

  const _ListSection({required this.title, required this.icon, required this.color, required this.items, required this.delay});

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const SizedBox();
    return _SectionCard(
      title: title,
      icon: icon,
      color: color,
      delay: delay,
      content: Column(
        children: items.map((item) => Padding(
          padding: const EdgeInsets.only(bottom: 12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                margin: const EdgeInsets.only(top: 6),
                width: 6, height: 6,
                decoration: BoxDecoration(color: color, shape: BoxShape.circle),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(item, style: GoogleFonts.inter(fontSize: 14, color: AppColors.textSecondary, height: 1.4)),
              ),
            ],
          ),
        )).toList(),
      ),
    );
  }
}
