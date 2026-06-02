import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:percent_indicator/percent_indicator.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/features/analysis/providers/analysis_provider.dart';
import 'package:lexguard_ai/models/analysis_model.dart';
import 'package:lexguard_ai/models/document_model.dart';
import 'package:lexguard_ai/features/clauses/screens/clauses_screen.dart';
import 'package:lexguard_ai/features/chat/screens/chat_screen.dart';
import 'package:lexguard_ai/features/chat/providers/chat_provider.dart';
import 'package:intl/intl.dart';

class AnalysisScreen extends StatefulWidget {
  final String? documentId;
  const AnalysisScreen({super.key, this.documentId});

  @override
  State<AnalysisScreen> createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AnalysisProvider>().loadAnalysis(widget.documentId ?? '1');
    });
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AnalysisProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        leading: IconButton(
          onPressed: () => Navigator.pop(context),
          icon: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(color: AppColors.cardDark, borderRadius: BorderRadius.circular(10), border: Border.all(color: AppColors.border)),
            child: Icon(Icons.arrow_back_ios_new, size: 16, color: AppColors.textPrimary),
          ),
        ),
        title: Text('AI Analysis', style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
        actions: [
          IconButton(
            onPressed: () {},
            icon: Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: AppColors.cardDark, borderRadius: BorderRadius.circular(10), border: Border.all(color: AppColors.border)),
              child: const Icon(Icons.ios_share_outlined, size: 18, color: AppColors.gold),
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: provider.isLoading
          ? _LoadingView()
          : provider.analysis == null
              ? const Center(child: Text('No analysis available'))
              : _AnalysisContent(analysis: provider.analysis!, documentId: widget.documentId ?? provider.analysis!.documentId),
    );
  }
}

class _LoadingView extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80, height: 80,
            decoration: BoxDecoration(color: AppColors.goldGlow, shape: BoxShape.circle),
            child: const Icon(Icons.psychology_outlined, color: AppColors.gold, size: 42),
          ).animate(onPlay: (c) => c.repeat(reverse: true)).scale(begin: const Offset(0.9, 0.9), end: const Offset(1.1, 1.1), duration: 1000.ms),
          const SizedBox(height: 24),
          Text('AI Analyzing Document...', style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
          const SizedBox(height: 8),
          Text('Extracting clauses, detecting risks', style: GoogleFonts.inter(fontSize: 14, color: AppColors.textSecondary)),
          const SizedBox(height: 32),
          SizedBox(width: 200, child: LinearProgressIndicator(valueColor: AlwaysStoppedAnimation(AppColors.gold), backgroundColor: AppColors.border, minHeight: 3)),
        ],
      ),
    );
  }
}

class _AnalysisContent extends StatelessWidget {
  final AnalysisModel analysis;
  final String documentId;
  const _AnalysisContent({required this.analysis, required this.documentId});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Doc Name
          Text(analysis.documentName, style: GoogleFonts.inter(fontSize: 14, color: AppColors.textSecondary), maxLines: 1, overflow: TextOverflow.ellipsis),
          const SizedBox(height: 16),

          // Risk Score Card
          _RiskScoreCard(analysis: analysis).animate().fadeIn().slideY(begin: 0.2, end: 0),
          const SizedBox(height: 16),

          // Action Buttons
          Row(children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ClausesScreen())),
                style: OutlinedButton.styleFrom(side: BorderSide(color: AppColors.border), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)), padding: EdgeInsets.symmetric(vertical: 12)),
                icon: const Icon(Icons.article_outlined, size: 18, color: AppColors.gold),
                label: Text('Clauses', style: GoogleFonts.inter(color: AppColors.textPrimary, fontWeight: FontWeight.w600, fontSize: 13)),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () {
                  debugPrint('[AnalysisScreen] Navigating to ChatScreen: documentId=$documentId, name=${analysis.documentName}');
                  // Set full context (id + name) before pushing so ChatScreen.initState
                  // skips the redundant setDocumentContext call, preserving documentName.
                  context.read<ChatProvider>().setDocumentContext(
                    documentId,
                    documentName: analysis.documentName,
                  );
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (ctx) => ChatScreen(
                        documentId: documentId,
                        documentName: analysis.documentName,
                      ),
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(backgroundColor: AppColors.gold, foregroundColor: AppColors.navy, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)), padding: const EdgeInsets.symmetric(vertical: 12)),
                icon: const Icon(Icons.chat_bubble_outline, size: 18),
                label: Text('Chat', style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 13)),
              ),
            ),
          ]).animate(delay: 100.ms).fadeIn(),

          const SizedBox(height: 20),

          // Summary Section
          _SectionCard(
            title: '📋 Document Summary',
            child: Text(analysis.summary, style: GoogleFonts.inter(fontSize: 14, color: AppColors.textSecondary, height: 1.6)),
          ).animate(delay: 150.ms).fadeIn().slideY(begin: 0.1, end: 0),

          const SizedBox(height: 16),

          // Parties
          _SectionCard(
            title: '👥 Parties Involved',
            child: Column(
              children: analysis.parties.map((p) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(children: [
                  Container(width: 8, height: 8, decoration: BoxDecoration(color: AppColors.gold, shape: BoxShape.circle)),
                  const SizedBox(width: 10),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(p.name, style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
                    Text('${p.role} • ${p.jurisdiction}', style: GoogleFonts.inter(fontSize: 12, color: AppColors.textSecondary)),
                  ])),
                ]),
              )).toList(),
            ),
          ).animate(delay: 200.ms).fadeIn().slideY(begin: 0.1, end: 0),

          const SizedBox(height: 16),

          // Important Dates
          _SectionCard(
            title: '📅 Important Dates',
            child: Column(
              children: analysis.importantDates.map((d) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(color: AppColors.goldGlow, borderRadius: BorderRadius.circular(8)),
                    child: Text(DateFormat('MMM d, yyyy').format(d.date), style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.gold)),
                  ),
                  const SizedBox(width: 12),
                  Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(d.label, style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
                    Text(d.description, style: GoogleFonts.inter(fontSize: 11, color: AppColors.textSecondary)),
                  ])),
                ]),
              )).toList(),
            ),
          ).animate(delay: 250.ms).fadeIn().slideY(begin: 0.1, end: 0),

          const SizedBox(height: 16),

          // Key Clauses
          _SectionCard(
            title: '⚖️ Key Clauses',
            child: Column(
              children: analysis.keyClauses.take(3).map((c) => _ClauseRow(clause: c)).toList(),
            ),
          ).animate(delay: 300.ms).fadeIn().slideY(begin: 0.1, end: 0),

          const SizedBox(height: 16),

          // Obligations
          _SectionCard(
            title: '📌 Obligations',
            child: Column(
              children: analysis.obligations.asMap().entries.map((e) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('${e.key + 1}.', style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.gold)),
                  const SizedBox(width: 8),
                  Expanded(child: Text(e.value, style: GoogleFonts.inter(fontSize: 13, color: AppColors.textSecondary, height: 1.5))),
                ]),
              )).toList(),
            ),
          ).animate(delay: 350.ms).fadeIn().slideY(begin: 0.1, end: 0),

          const SizedBox(height: 16),

          // Recommendations
          _SectionCard(
            title: '💡 AI Recommendations',
            child: Column(
              children: analysis.recommendations.map((r) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 5),
                child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Icon(Icons.lightbulb_outline, size: 16, color: AppColors.gold),
                  const SizedBox(width: 8),
                  Expanded(child: Text(r, style: GoogleFonts.inter(fontSize: 13, color: AppColors.textSecondary, height: 1.5))),
                ]),
              )).toList(),
            ),
          ).animate(delay: 400.ms).fadeIn().slideY(begin: 0.1, end: 0),

          const SizedBox(height: 16),

          // Legal Disclaimer
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color: AppColors.warningBg, borderRadius: BorderRadius.circular(12), border: Border.all(color: AppColors.warning.withValues(alpha: 0.3))),
            child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Icon(Icons.info_outline, color: AppColors.warning, size: 16),
              const SizedBox(width: 10),
              Expanded(child: Text(
                'AI Disclaimer: This analysis is for informational purposes only and does not constitute legal advice. Please consult a qualified attorney before making legal decisions.',
                style: GoogleFonts.inter(fontSize: 11, color: AppColors.warning, height: 1.5),
              )),
            ]),
          ).animate(delay: 450.ms).fadeIn(),

          const SizedBox(height: 32),
        ],
      ),
    );
  }
}

class _RiskScoreCard extends StatelessWidget {
  final AnalysisModel analysis;
  const _RiskScoreCard({required this.analysis});

  @override
  Widget build(BuildContext context) {
    final riskColor = analysis.riskLevel == RiskLevel.high ? AppColors.highRisk : analysis.riskLevel == RiskLevel.medium ? AppColors.mediumRisk : AppColors.lowRisk;
    final riskBg = analysis.riskLevel == RiskLevel.high ? AppColors.highRiskBg : analysis.riskLevel == RiskLevel.medium ? AppColors.mediumRiskBg : AppColors.lowRiskBg;
    final riskLabel = analysis.riskLevel == RiskLevel.high ? 'HIGH RISK' : analysis.riskLevel == RiskLevel.medium ? 'MEDIUM RISK' : 'LOW RISK';

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [AppColors.cardMid, AppColors.cardDark]),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: riskColor.withValues(alpha: 0.3)),
        boxShadow: [BoxShadow(color: riskColor.withValues(alpha: 0.1), blurRadius: 16)],
      ),
      child: Row(children: [
        CircularPercentIndicator(
          radius: 52,
          lineWidth: 8,
          percent: analysis.riskScore / 100,
          center: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            Text('${analysis.riskScore}', style: GoogleFonts.inter(fontSize: 22, fontWeight: FontWeight.w800, color: riskColor)),
            Text('/100', style: GoogleFonts.inter(fontSize: 11, color: AppColors.textHint)),
          ]),
          progressColor: riskColor,
          backgroundColor: riskColor.withValues(alpha: 0.15),
          circularStrokeCap: CircularStrokeCap.round,
        ),
        const SizedBox(width: 20),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(color: riskBg, borderRadius: BorderRadius.circular(6)),
            child: Text(riskLabel, style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w800, color: riskColor)),
          ),
          const SizedBox(height: 10),
          Text('Risk Score', style: GoogleFonts.inter(fontSize: 13, color: AppColors.textSecondary)),
          const SizedBox(height: 4),
          Row(children: [
            const Icon(Icons.psychology_outlined, size: 14, color: AppColors.gold),
            const SizedBox(width: 4),
            Text('AI Confidence: ${analysis.aiConfidence}%', style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.gold)),
          ]),
          const SizedBox(height: 8),
          Text('${analysis.keyClauses.length} clauses • ${analysis.parties.length} parties', style: GoogleFonts.inter(fontSize: 12, color: AppColors.textHint)),
        ])),
      ]),
    );
  }
}

class _SectionCard extends StatefulWidget {
  final String title;
  final Widget child;
  const _SectionCard({required this.title, required this.child});

  @override
  State<_SectionCard> createState() => _SectionCardState();
}

class _SectionCardState extends State<_SectionCard> {
  bool _expanded = true;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(color: AppColors.cardDark, borderRadius: BorderRadius.circular(16), border: Border.all(color: AppColors.border)),
      child: Column(children: [
        InkWell(
          onTap: () => setState(() => _expanded = !_expanded),
          borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(children: [
              Expanded(child: Text(widget.title, style: GoogleFonts.inter(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.textPrimary))),
              Icon(_expanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down, color: AppColors.textHint),
            ]),
          ),
        ),
        if (_expanded) ...[
          Divider(color: AppColors.border, height: 1),
          Padding(padding: const EdgeInsets.all(16), child: widget.child),
        ],
      ]),
    );
  }
}

class _ClauseRow extends StatelessWidget {
  final KeyClause clause;
  const _ClauseRow({required this.clause});

  @override
  Widget build(BuildContext context) {
    final riskColor = clause.risk == RiskLevel.high ? AppColors.highRisk : clause.risk == RiskLevel.medium ? AppColors.mediumRisk : AppColors.lowRisk;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(children: [
        Container(width: 10, height: 10, decoration: BoxDecoration(color: riskColor, shape: BoxShape.circle)),
        const SizedBox(width: 10),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(clause.title, style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
          Text(clause.summary, style: GoogleFonts.inter(fontSize: 11, color: AppColors.textSecondary), maxLines: 2, overflow: TextOverflow.ellipsis),
        ])),
      ]),
    );
  }
}
