import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/models/clause_model.dart';
import 'package:lexguard_ai/models/document_model.dart';

class ClausesScreen extends StatelessWidget {
  const ClausesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final clauses = ClauseModel.dummyClauses;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        leading: IconButton(
          onPressed: () => Navigator.pop(context),
          icon: Container(padding: EdgeInsets.all(8), decoration: BoxDecoration(color: AppColors.cardDark, borderRadius: BorderRadius.circular(10), border: Border.all(color: AppColors.border)), child: Icon(Icons.arrow_back_ios_new, size: 16, color: AppColors.textPrimary)),
        ),
        title: Text('Clause Extraction', style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
        actions: [
          IconButton(
            onPressed: () {},
            icon: Container(padding: const EdgeInsets.all(8), decoration: BoxDecoration(color: AppColors.cardDark, borderRadius: BorderRadius.circular(10), border: Border.all(color: AppColors.border)), child: const Icon(Icons.filter_list_rounded, size: 18, color: AppColors.gold)),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
            child: Row(children: [
              const Icon(Icons.article_outlined, color: AppColors.gold, size: 16),
              const SizedBox(width: 8),
              Text('${clauses.length} clauses detected', style: GoogleFonts.inter(fontSize: 13, color: AppColors.textSecondary)),
              const Spacer(),
              Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4), decoration: BoxDecoration(color: AppColors.goldGlow, borderRadius: BorderRadius.circular(8)), child: Text('AI Extracted', style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.gold))),
            ]),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              itemCount: clauses.length,
              itemBuilder: (context, i) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _ClauseCard(clause: clauses[i]),
              ).animate(delay: Duration(milliseconds: i * 70)).fadeIn().slideX(begin: 0.05, end: 0),
            ),
          ),
        ],
      ),
    );
  }
}

class _ClauseCard extends StatefulWidget {
  final ClauseModel clause;
  const _ClauseCard({required this.clause});

  @override
  State<_ClauseCard> createState() => _ClauseCardState();
}

class _ClauseCardState extends State<_ClauseCard> {
  bool _expanded = false;

  Color get _riskColor {
    switch (widget.clause.risk) {
      case RiskLevel.high:
        return AppColors.highRisk;
      case RiskLevel.medium:
        return AppColors.mediumRisk;
      case RiskLevel.low:
        return AppColors.lowRisk;
    }
  }

  String get _riskLabel {
    switch (widget.clause.risk) {
      case RiskLevel.high:
        return 'HIGH';
      case RiskLevel.medium:
        return 'MEDIUM';
      case RiskLevel.low:
        return 'LOW';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.cardDark,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _expanded ? _riskColor.withValues(alpha: 0.3) : AppColors.border),
        boxShadow: _expanded ? [BoxShadow(color: _riskColor.withValues(alpha: 0.08), blurRadius: 12)] : [],
      ),
      child: Column(
        children: [
          // Header
          InkWell(
            onTap: () => setState(() => _expanded = !_expanded),
            borderRadius: BorderRadius.vertical(top: const Radius.circular(16), bottom: Radius.circular(_expanded ? 0 : 16)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Container(
                  width: 40, height: 40,
                  decoration: BoxDecoration(color: _riskColor.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
                  child: const Icon(Icons.article_outlined, size: 20, color: AppColors.gold),
                ),
                const SizedBox(width: 12),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Expanded(child: Text(widget.clause.title, style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.textPrimary))),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(color: _riskColor.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(6)),
                      child: Text(_riskLabel, style: GoogleFonts.inter(fontSize: 10, fontWeight: FontWeight.w800, color: _riskColor)),
                    ),
                  ]),
                  const SizedBox(height: 4),
                  Text(widget.clause.category, style: GoogleFonts.inter(fontSize: 11, color: AppColors.textHint)),
                  const SizedBox(height: 6),
                  Text(widget.clause.summary, style: GoogleFonts.inter(fontSize: 12, color: AppColors.textSecondary, height: 1.4), maxLines: _expanded ? null : 2, overflow: _expanded ? null : TextOverflow.ellipsis),
                ])),
                const SizedBox(width: 8),
                Icon(_expanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down, color: AppColors.textHint, size: 20),
              ]),
            ),
          ),

          // Expanded Content
          if (_expanded) ...[
            Divider(color: AppColors.border, height: 1),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                // Full text
                Text('Clause Text', style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.textHint, letterSpacing: 0.5)),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: AppColors.cardMid, borderRadius: BorderRadius.circular(10), border: Border.all(color: AppColors.border)),
                  child: Text(widget.clause.content, style: GoogleFonts.inter(fontSize: 12, color: AppColors.textSecondary, height: 1.6, fontStyle: FontStyle.italic)),
                ),

                const SizedBox(height: 14),

                // AI Explanation
                Text('AI Analysis', style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.textHint, letterSpacing: 0.5)),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: _riskColor.withValues(alpha: 0.07), borderRadius: BorderRadius.circular(10), border: Border.all(color: _riskColor.withValues(alpha: 0.2))),
                  child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Icon(Icons.psychology_outlined, size: 16, color: _riskColor),
                    const SizedBox(width: 8),
                    Expanded(child: Text(widget.clause.explanation, style: GoogleFonts.inter(fontSize: 12, color: AppColors.textSecondary, height: 1.5))),
                  ]),
                ),

                const SizedBox(height: 14),

                // Keywords
                Text('Key Terms', style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w700, color: AppColors.textHint, letterSpacing: 0.5)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6, runSpacing: 6,
                  children: widget.clause.keywords.map((kw) => Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(color: AppColors.navyAccent, borderRadius: BorderRadius.circular(6), border: Border.all(color: AppColors.border)),
                    child: Text(kw, style: GoogleFonts.inter(fontSize: 11, color: AppColors.gold, fontWeight: FontWeight.w600)),
                  )).toList(),
                ),
              ]),
            ),
          ],
        ],
      ),
    );
  }
}
