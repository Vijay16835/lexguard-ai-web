import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/features/upload/providers/document_provider.dart';
import 'package:lexguard_ai/features/chat/screens/document_chat_screen.dart';

class AnalysisResultScreen extends StatefulWidget {
  final String documentId;
  const AnalysisResultScreen({super.key, required this.documentId});

  @override
  State<AnalysisResultScreen> createState() => _AnalysisResultScreenState();
}

class _AnalysisResultScreenState extends State<AnalysisResultScreen> {
  Timer? _pollTimer;
  bool _isAnalyzing = true;

  @override
  void initState() {
    super.initState();
    _loadDocument();
  }

  Future<void> _loadDocument() async {
    final provider = context.read<DocumentProvider>();
    await provider.fetchDocumentDetail(widget.documentId);

    if (!mounted) return;

    final doc = provider.currentDocument;
    if (doc != null && (doc['status'] == 'completed' || doc['status'] == 'failed')) {
      setState(() => _isAnalyzing = false);
    } else {
      // Start polling
      _pollTimer = Timer.periodic(const Duration(seconds: 3), (timer) async {
        await provider.fetchDocumentDetail(widget.documentId);
        if (!mounted) {
          timer.cancel();
          return;
        }
        final updatedDoc = provider.currentDocument;
        if (updatedDoc != null &&
            (updatedDoc['status'] == 'completed' || updatedDoc['status'] == 'failed')) {
          timer.cancel();
          setState(() => _isAnalyzing = false);
        }
      });
    }
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Color _riskColor(String? level) {
    switch (level?.toLowerCase()) {
      case 'high':
        return const Color(0xFFEF4444);
      case 'medium':
        return const Color(0xFFF59E0B);
      case 'low':
        return const Color(0xFF22C55E);
      default:
        return AppColors.textSecondary;
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<DocumentProvider>();
    final doc = provider.currentDocument;
    final analysis = provider.currentAnalysis;
    final clauses = provider.currentClauses;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          doc?['name'] ?? 'Analysis',
          style: GoogleFonts.inter(
              fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
          overflow: TextOverflow.ellipsis,
        ),
        actions: [
          if (!_isAnalyzing && doc?['status'] == 'completed')
            IconButton(
              icon: const Icon(Icons.chat_bubble_outline, color: AppColors.gold),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => DocumentChatScreen(
                      documentId: widget.documentId,
                      documentName: doc?['name'] ?? 'Document',
                    ),
                  ),
                );
              },
            ),
        ],
      ),
      body: _isAnalyzing ? _buildLoadingView() : _buildResultView(doc, analysis, clauses),
    );
  }

  Widget _buildLoadingView() {
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
            child: const CircularProgressIndicator(color: AppColors.gold, strokeWidth: 3),
          ).animate(onPlay: (c) => c.repeat()).shimmer(duration: 1500.ms),
          const SizedBox(height: 32),
          Text('AI is analyzing your document...',
              style: GoogleFonts.inter(
                  fontSize: 18, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
          const SizedBox(height: 8),
          Text('This may take 15-30 seconds',
              style: GoogleFonts.inter(fontSize: 14, color: AppColors.textSecondary)),
        ],
      ),
    );
  }

  Widget _buildResultView(
    Map<String, dynamic>? doc,
    Map<String, dynamic>? analysis,
    List<Map<String, dynamic>> clauses,
  ) {
    if (doc == null) {
      return Center(
        child: Text('Failed to load document',
            style: GoogleFonts.inter(color: AppColors.textSecondary)),
      );
    }

    if (doc['status'] == 'failed') {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: AppColors.error),
            const SizedBox(height: 16),
            Text('Analysis Failed',
                style: GoogleFonts.inter(
                    fontSize: 20, fontWeight: FontWeight.w700, color: AppColors.error)),
            const SizedBox(height: 8),
            Text('The document could not be analyzed.',
                style: GoogleFonts.inter(fontSize: 14, color: AppColors.textSecondary)),
          ],
        ),
      );
    }

    final rawData = analysis?['raw_data'] as Map<String, dynamic>? ?? {};

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Risk Score Card
          _buildRiskCard(doc).animate().fadeIn().slideY(begin: 0.2, end: 0),
          const SizedBox(height: 20),

          // Summary
          _buildSection(
            'AI Summary',
            Icons.auto_awesome,
            doc['summary'] ?? 'No summary available',
          ).animate().fadeIn(delay: 100.ms),
          const SizedBox(height: 16),

          // Key Points
          if (rawData['key_points'] != null && (rawData['key_points'] as List).isNotEmpty)
            _buildListSection(
              'Key Points',
              Icons.star_outline,
              List<String>.from(rawData['key_points']),
            ).animate().fadeIn(delay: 200.ms),

          if (rawData['key_points'] != null && (rawData['key_points'] as List).isNotEmpty)
            const SizedBox(height: 16),

          // Parties
          if (analysis?['parties'] != null && (analysis!['parties'] as List).isNotEmpty)
            _buildChipSection(
              'Involved Parties',
              Icons.people_outline,
              List<String>.from(analysis['parties']),
            ).animate().fadeIn(delay: 250.ms),

          if (analysis?['parties'] != null && (analysis!['parties'] as List).isNotEmpty)
            const SizedBox(height: 16),

          // Risks
          if (rawData['risks'] != null && (rawData['risks'] as List).isNotEmpty)
            _buildRisksSection(List<Map<String, dynamic>>.from(rawData['risks']))
                .animate()
                .fadeIn(delay: 300.ms),

          if (rawData['risks'] != null && (rawData['risks'] as List).isNotEmpty)
            const SizedBox(height: 16),

          // Clauses
          if (clauses.isNotEmpty)
            _buildClausesSection(clauses).animate().fadeIn(delay: 350.ms),
          if (clauses.isNotEmpty) const SizedBox(height: 16),

          // Recommendations
          if (analysis?['recommendations'] != null &&
              (analysis!['recommendations'] as List).isNotEmpty)
            _buildListSection(
              'Recommendations',
              Icons.lightbulb_outline,
              List<String>.from(analysis['recommendations']),
            ).animate().fadeIn(delay: 400.ms),

          const SizedBox(height: 24),

          // Chat button
          SizedBox(
            width: double.infinity,
            height: 56,
            child: ElevatedButton.icon(
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => DocumentChatScreen(
                      documentId: widget.documentId,
                      documentName: doc['name'] ?? 'Document',
                    ),
                  ),
                );
              },
              icon: const Icon(Icons.chat_bubble_outline),
              label: Text('Chat with this Document',
                  style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w700)),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.gold,
                foregroundColor: AppColors.navy,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
            ),
          ).animate().fadeIn(delay: 500.ms),

          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildRiskCard(Map<String, dynamic> doc) {
    final score = doc['risk_score'] ?? 0;
    final level = doc['risk_level'] ?? 'Unknown';
    final color = _riskColor(level);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [color.withOpacity(0.15), color.withOpacity(0.05)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          // Score circle
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: color, width: 4),
            ),
            child: Center(
              child: Text(
                '$score',
                style: GoogleFonts.inter(
                    fontSize: 28, fontWeight: FontWeight.w800, color: color),
              ),
            ),
          ),
          const SizedBox(width: 20),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Risk Score',
                    style: GoogleFonts.inter(
                        fontSize: 13, color: AppColors.textSecondary)),
                const SizedBox(height: 4),
                Text(
                  '$level Risk',
                  style: GoogleFonts.inter(
                      fontSize: 24, fontWeight: FontWeight.w800, color: color),
                ),
                const SizedBox(height: 4),
                Text(
                  doc['document_type'] ?? '',
                  style: GoogleFonts.inter(
                      fontSize: 13, color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSection(String title, IconData icon, String content) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
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
              Icon(icon, size: 20, color: AppColors.gold),
              const SizedBox(width: 8),
              Text(title,
                  style: GoogleFonts.inter(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary)),
            ],
          ),
          const SizedBox(height: 12),
          Text(content,
              style: GoogleFonts.inter(
                  fontSize: 13, color: AppColors.textSecondary, height: 1.6)),
        ],
      ),
    );
  }

  Widget _buildListSection(String title, IconData icon, List<String> items) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
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
              Icon(icon, size: 20, color: AppColors.gold),
              const SizedBox(width: 8),
              Text(title,
                  style: GoogleFonts.inter(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary)),
            ],
          ),
          const SizedBox(height: 12),
          ...items.map((item) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('  •  ',
                        style: TextStyle(color: AppColors.gold, fontSize: 14)),
                    Expanded(
                      child: Text(item,
                          style: GoogleFonts.inter(
                              fontSize: 13,
                              color: AppColors.textSecondary,
                              height: 1.5)),
                    ),
                  ],
                ),
              )),
        ],
      ),
    );
  }

  Widget _buildChipSection(String title, IconData icon, List<String> items) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
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
              Icon(icon, size: 20, color: AppColors.gold),
              const SizedBox(width: 8),
              Text(title,
                  style: GoogleFonts.inter(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary)),
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: items
                .map((item) => Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: AppColors.goldGlow,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(item,
                          style: GoogleFonts.inter(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: AppColors.gold)),
                    ))
                .toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildRisksSection(List<Map<String, dynamic>> risks) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
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
              const Icon(Icons.warning_amber, size: 20, color: AppColors.gold),
              const SizedBox(width: 8),
              Text('Identified Risks',
                  style: GoogleFonts.inter(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary)),
            ],
          ),
          const SizedBox(height: 12),
          ...risks.map((risk) => Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: _riskColor(risk['severity']).withOpacity(0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                      color: _riskColor(risk['severity']).withOpacity(0.2)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: _riskColor(risk['severity']).withOpacity(0.2),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            risk['severity'] ?? 'N/A',
                            style: GoogleFonts.inter(
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                color: _riskColor(risk['severity'])),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            risk['category'] ?? '',
                            style: GoogleFonts.inter(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                color: AppColors.textPrimary),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      risk['description'] ?? '',
                      style: GoogleFonts.inter(
                          fontSize: 12,
                          color: AppColors.textSecondary,
                          height: 1.5),
                    ),
                  ],
                ),
              )),
        ],
      ),
    );
  }

  Widget _buildClausesSection(List<Map<String, dynamic>> clauses) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
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
              const Icon(Icons.gavel, size: 20, color: AppColors.gold),
              const SizedBox(width: 8),
              Text('Key Clauses',
                  style: GoogleFonts.inter(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary)),
            ],
          ),
          const SizedBox(height: 12),
          ...clauses.take(5).map((clause) => Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.background,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: _riskColor(clause['risk_level']).withOpacity(0.2),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            clause['risk_level'] ?? 'Low',
                            style: GoogleFonts.inter(
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                color: _riskColor(clause['risk_level'])),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            clause['title'] ?? '',
                            style: GoogleFonts.inter(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                color: AppColors.textPrimary),
                          ),
                        ),
                      ],
                    ),
                    if (clause['summary'] != null &&
                        clause['summary'].toString().isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Text(
                        clause['summary'],
                        style: GoogleFonts.inter(
                            fontSize: 12,
                            color: AppColors.textSecondary,
                            height: 1.4),
                      ),
                    ],
                  ],
                ),
              )),
        ],
      ),
    );
  }
}
