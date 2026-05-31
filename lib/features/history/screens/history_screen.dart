import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:open_filex/open_filex.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/features/history/providers/history_provider.dart';
import 'package:lexguard_ai/models/document_model.dart';
import 'package:lexguard_ai/widgets/cards/document_card.dart';
import 'package:lexguard_ai/features/analysis/screens/analysis_screen.dart';
import 'package:lexguard_ai/features/auth/providers/auth_provider.dart';
import 'package:lexguard_ai/features/profile/providers/profile_provider.dart';


class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<HistoryProvider>().loadHistory();
    });
  }

  @override
  Widget build(BuildContext context) {
    final history = context.watch<HistoryProvider>();
    context.watch<ProfileProvider>();

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: Text('Document History', style: GoogleFonts.inter(fontSize: 24, fontWeight: FontWeight.w800, color: AppColors.textPrimary)),
            ),

            // Search Bar
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: TextField(
                onChanged: (v) => context.read<HistoryProvider>().search(v),
                style: GoogleFonts.inter(fontSize: 14, color: AppColors.textPrimary),
                decoration: InputDecoration(
                  hintText: 'Search documents...',
                  hintStyle: GoogleFonts.inter(fontSize: 14, color: AppColors.textHint),
                  prefixIcon: Icon(Icons.search, color: AppColors.textHint, size: 20),
                  filled: true,
                  fillColor: AppColors.cardDark,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: AppColors.border)),
                  enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: AppColors.border)),
                  focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.gold)),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                ),
              ),
            ).animate().fadeIn(duration: 400.ms),

            // Filter Chips
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 12, 0, 0),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(children: [
                  _FilterChip(label: 'All', isSelected: history.riskFilter == null, onTap: () => context.read<HistoryProvider>().setRiskFilter(null)),
                  _FilterChip(label: '🔴 High Risk', isSelected: history.riskFilter == RiskLevel.high, onTap: () => context.read<HistoryProvider>().setRiskFilter(RiskLevel.high), color: AppColors.highRisk),
                  _FilterChip(label: '🟡 Medium', isSelected: history.riskFilter == RiskLevel.medium, onTap: () => context.read<HistoryProvider>().setRiskFilter(RiskLevel.medium), color: AppColors.mediumRisk),
                  _FilterChip(label: '🟢 Low Risk', isSelected: history.riskFilter == RiskLevel.low, onTap: () => context.read<HistoryProvider>().setRiskFilter(RiskLevel.low), color: AppColors.lowRisk),
                ]),
              ),
            ).animate(delay: 100.ms).fadeIn(),

            // Count & Sort
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('${history.documents.length} documents', style: GoogleFonts.inter(fontSize: 13, color: AppColors.textHint)),
                  PopupMenuButton<DocumentSortOption>(
                    initialValue: history.sortOption,
                    color: AppColors.cardMid,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    onSelected: (opt) => context.read<HistoryProvider>().setSortOption(opt),
                    itemBuilder: (context) => [
                      PopupMenuItem(value: DocumentSortOption.date, child: Text('Sort by Date', style: GoogleFonts.inter(color: AppColors.textPrimary))),
                      PopupMenuItem(value: DocumentSortOption.type, child: Text('Sort by Type', style: GoogleFonts.inter(color: AppColors.textPrimary))),
                      PopupMenuItem(value: DocumentSortOption.status, child: Text('Sort by Status', style: GoogleFonts.inter(color: AppColors.textPrimary))),
                    ],
                    child: Row(
                      children: [
                        Text('Sort', style: GoogleFonts.inter(fontSize: 13, color: AppColors.textHint)),
                        const SizedBox(width: 4),
                        Icon(Icons.sort, color: AppColors.textHint, size: 16),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // List
            Expanded(
              child: history.isLoading
                  ? const Center(child: CircularProgressIndicator(color: AppColors.gold))
                  : history.errorMessage != null
                      ? Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.error_outline, color: AppColors.error, size: 48),
                              const SizedBox(height: 16),
                              Text(history.errorMessage!, style: GoogleFonts.inter(color: AppColors.textPrimary)),
                              const SizedBox(height: 16),
                              ElevatedButton(
                                onPressed: () => context.read<HistoryProvider>().loadHistory(),
                                style: ElevatedButton.styleFrom(backgroundColor: AppColors.gold, foregroundColor: AppColors.navy),
                                child: const Text('Retry'),
                              ),
                            ],
                          ),
                        )
                      : history.documents.isEmpty
                          ? _EmptyState()
                          : ListView.builder(
                              padding: const EdgeInsets.symmetric(horizontal: 20),
                              itemCount: history.documents.length,
                              itemBuilder: (context, i) {
                                final doc = history.documents[i];
                                return Padding(
                                  padding: const EdgeInsets.only(bottom: 10),
                                  child: DocumentCard(
                                    document: doc,
                                    showDelete: true,
                                    onTap: () => _showDocumentActions(context, doc),
                                    onDelete: () => _deleteDoc(context, doc),
                                  ),
                                ).animate(delay: Duration(milliseconds: i * 60)).fadeIn().slideX(begin: 0.05, end: 0);
                              },
                            ),
            ),
          ],
        ),
      ),
    );
  }

  void _deleteDoc(BuildContext context, DocumentModel doc) async {
    final success = await context.read<HistoryProvider>().deleteDocument(doc.id);
    if (success && context.mounted) {
      // Recalculate usage immediately by fetching updated user profile
      await context.read<AuthProvider>().checkInitialAuth();
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Document deleted from database and storage', style: GoogleFonts.inter(color: Colors.white)),
          backgroundColor: AppColors.success,
        ),
      );
    }
  }

  Future<void> _openDocument(BuildContext context, DocumentModel doc) async {
    final provider = context.read<HistoryProvider>();
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => const Center(child: CircularProgressIndicator(color: AppColors.gold)),
    );

    final success = await provider.openDocument(doc.path, fileName: doc.name);
    if (!context.mounted) return;

    Navigator.pop(context);
    if (!success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Unable to open the file. It may be missing or unsupported.',
            style: GoogleFonts.inter(color: Colors.white),
          ),
          backgroundColor: AppColors.error,
        ),
      );
    }
  }

  Future<void> _downloadReport(BuildContext context, DocumentModel doc, String format) async {
    final provider = context.read<HistoryProvider>();
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.cardDark,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        content: SizedBox(
          width: double.infinity,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('Generating report', style: GoogleFonts.inter(color: AppColors.textPrimary, fontWeight: FontWeight.w700)),
              const SizedBox(height: 16),
              Consumer<HistoryProvider>(
                builder: (context, provider, _) {
                  return Column(
                    children: [
                      LinearProgressIndicator(value: provider.downloadProgress > 0 ? provider.downloadProgress : null, color: AppColors.gold, backgroundColor: AppColors.cardMid),
                      const SizedBox(height: 12),
                      Text(
                        provider.downloadProgress > 0
                            ? '${(provider.downloadProgress * 100).toStringAsFixed(0)}%'
                            : 'Preparing AI summary...',
                        style: GoogleFonts.inter(color: AppColors.textHint, fontSize: 12),
                      ),
                    ],
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );

    final path = await provider.downloadReport(doc.id, format: format);
    if (!context.mounted) return;

    Navigator.pop(context);
    if (path != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Report downloaded to: $path', style: GoogleFonts.inter(color: Colors.white)),
          backgroundColor: AppColors.success,
        ),
      );

      await OpenFilex.open(path);
    } else {
      final errorMessage = provider.errorMessage ?? 'Unable to download report. Please try again.';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(errorMessage, style: GoogleFonts.inter(color: Colors.white)),
          backgroundColor: AppColors.error,
        ),
      );
    }
  }

  void _showReportFormatDialog(BuildContext context, DocumentModel doc) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        String selectedFormat = 'pdf';
        final formats = [
          {'label': 'PDF', 'value': 'pdf', 'icon': Icons.picture_as_pdf},
          {'label': 'DOCX', 'value': 'docx', 'icon': Icons.description},
          {'label': 'TXT', 'value': 'txt', 'icon': Icons.text_snippet},
        ];

        return StatefulBuilder(
          builder: (ctx, setState) => Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: AppColors.cardDark,
              borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2)),
                  ),
                ).animate().fadeIn(duration: 250.ms),
                const SizedBox(height: 24),
                Text('Choose report format', style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
                const SizedBox(height: 8),
                Text('A summarized AI report will be saved to your Downloads folder.', style: GoogleFonts.inter(fontSize: 13, color: AppColors.textSecondary)),
                const SizedBox(height: 20),
                ...formats.map((format) {
                  return _ReportFormatItem(
                    label: format['label'] as String,
                    value: format['value'] as String,
                    selectedFormat: selectedFormat,
                    icon: format['icon'] as IconData,
                    onTap: () => setState(() => selectedFormat = format['value'] as String),
                  );
                }),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.pop(ctx);
                      _downloadReport(context, doc, selectedFormat);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.gold,
                      foregroundColor: AppColors.navy,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                    child: Text('Download Summary', style: GoogleFonts.inter(fontWeight: FontWeight.w700)),
                  ),
                ),
                const SizedBox(height: 12),
              ],
            ),
          ).animate().fadeIn(duration: 250.ms).slideY(begin: 0.1, end: 0),
        );
      },
    );
  }

  void _showDocumentActions(BuildContext context, DocumentModel doc) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: AppColors.cardDark,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40, height: 4,
                decoration: BoxDecoration(color: AppColors.border, borderRadius: BorderRadius.circular(2)),
              ),
            ),
            const SizedBox(height: 24),
            Text(doc.name, style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary), maxLines: 1, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 24),
            
            _ActionItem(
              icon: Icons.folder_open,
              label: 'Open Document',
              onTap: () {
                Navigator.pop(ctx);
                _openDocument(context, doc);
              },
            ),
            _ActionItem(
              icon: Icons.psychology_outlined,
              label: 'View Analysis',
              onTap: () {
                Navigator.pop(ctx);
                Navigator.push(context, MaterialPageRoute(builder: (_) => AnalysisScreen(documentId: doc.id)));
              },
            ),
            _ActionItem(
              icon: Icons.download_rounded,
              label: 'Download Report',
              onTap: () {
                Navigator.pop(ctx);
                _showReportFormatDialog(context, doc);
              },
            ),
            _ActionItem(
              icon: Icons.delete_outline_rounded,
              label: 'Delete Document',
              color: AppColors.error,
              onTap: () {
                Navigator.pop(ctx);
                _deleteDoc(context, doc);
              },
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _ActionItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final Color? color;

  const _ActionItem({required this.icon, required this.label, required this.onTap, this.color});

  @override
  Widget build(BuildContext context) {
    final c = color ?? AppColors.textPrimary;
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Row(
          children: [
            Icon(icon, color: c, size: 22),
            const SizedBox(width: 16),
            Text(label, style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w600, color: c)),
          ],
        ),
      ),
    );
  }
}

class _ReportFormatItem extends StatelessWidget {
  final String label;
  final String value;
  final String selectedFormat;
  final IconData icon;
  final VoidCallback onTap;

  const _ReportFormatItem({required this.label, required this.value, required this.selectedFormat, required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final bool selected = selectedFormat == value;
    return InkWell(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 14),
        decoration: BoxDecoration(
          color: selected ? AppColors.gold.withValues(alpha: 0.12) : AppColors.cardDark,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: selected ? AppColors.gold : AppColors.border),
        ),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: selected ? AppColors.gold.withValues(alpha: 0.15) : AppColors.cardMid,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: selected ? AppColors.gold : AppColors.textHint, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(child: Text(label, style: GoogleFonts.inter(fontSize: 15, color: AppColors.textPrimary))),
            Icon(selected ? Icons.check_circle : Icons.radio_button_unchecked, color: selected ? AppColors.gold : AppColors.textHint, size: 20),
          ],
        ),
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;
  final Color? color;

  const _FilterChip({required this.label, required this.isSelected, required this.onTap, this.color});

  @override
  Widget build(BuildContext context) {
    final c = color ?? AppColors.gold;
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? c.withValues(alpha: 0.15) : AppColors.cardDark,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: isSelected ? c : AppColors.border),
        ),
        child: Text(label, style: GoogleFonts.inter(fontSize: 12, fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500, color: isSelected ? c : AppColors.textSecondary)),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Stack(
            alignment: Alignment.center,
            children: [
              Container(
                width: 140,
                height: 140,
                decoration: BoxDecoration(
                  color: AppColors.cardDark,
                  borderRadius: BorderRadius.circular(28),
                ),
              ),
              Positioned(
                top: 18,
                left: 18,
                child: Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(color: AppColors.gold.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(16)),
                ),
              ),
              Positioned(
                bottom: 18,
                right: 18,
                child: Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(color: AppColors.gold.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(12)),
                ),
              ),
              Container(
                width: 92,
                height: 92,
                decoration: BoxDecoration(color: AppColors.background, borderRadius: BorderRadius.circular(20), border: Border.all(color: AppColors.border)),
                child: const Icon(Icons.folder_open, color: AppColors.gold, size: 42),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Text('No documents yet', style: GoogleFonts.inter(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
          const SizedBox(height: 8),
          Text('Upload your first contract or policy to generate an AI summary.', textAlign: TextAlign.center, style: GoogleFonts.inter(fontSize: 13, color: AppColors.textSecondary, height: 1.5)),
        ],
      ),
    );
  }
}
