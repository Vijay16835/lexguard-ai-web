import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:file_picker/file_picker.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/features/upload/providers/document_provider.dart';
import 'package:lexguard_ai/features/analysis/screens/analysis_result_screen.dart';
import 'package:lexguard_ai/features/auth/providers/auth_provider.dart';
import 'package:lexguard_ai/features/history/providers/history_provider.dart';
import 'package:lexguard_ai/widgets/cards/document_card.dart';

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  PlatformFile? _selectedPlatformFile;
  String? _fileName;
  String? _fileSize;

  // Analysis options checkboxes
  bool _ocrDetection = true;
  bool _clauseExtraction = true;
  bool _riskAnalysis = true;
  bool _aiSummary = true;
  bool _keyDates = true;
  bool _importantParties = true;

  // Upload stages & simulation
  Timer? _stageTimer;
  String _currentStageText = "Uploading...";
  double _stageProgress = 0.0;
  bool _isAnalyzing = false;
  Map<String, dynamic>? _completedDocData;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<HistoryProvider>().loadHistory();
    });
  }

  @override
  void dispose() {
    _stageTimer?.cancel();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'docx', 'doc', 'txt', 'jpg', 'jpeg', 'png', 'webp'],
      withData: true, // Required on Flutter Web: loads file.bytes; without this, bytes is null and upload fails immediately
    );

    if (result != null) {
      final file = result.files.single;
      final double size = file.size / (1024 * 1024);
      debugPrint('[FILE_SELECTED] Selected file: ${file.name}, size: ${size.toStringAsFixed(2)} MB');
      setState(() {
        _selectedPlatformFile = file;
        _fileName = file.name;
        _fileSize = '${size.toStringAsFixed(2)} MB';
        _completedDocData = null; // Reset success state
      });
    }
  }

  void _removeSelectedFile() {
    setState(() {
      _selectedPlatformFile = null;
      _fileName = null;
      _fileSize = null;
      _completedDocData = null;
    });
  }

  void _startProgressSimulation() {
    setState(() {
      _isAnalyzing = true;
      _stageProgress = 0.0;
      _currentStageText = "Uploading...";
    });

    _stageTimer = Timer.periodic(const Duration(milliseconds: 150), (timer) {
      if (!mounted) return;
      setState(() {
        _stageProgress += 0.015;
        if (_stageProgress > 0.95) _stageProgress = 0.95; // Hold near end until actual resolve

        if (_stageProgress < 0.25) {
          _currentStageText = "Uploading...";
        } else if (_stageProgress < 0.50) {
          _currentStageText = "Extracting Text...";
        } else if (_stageProgress < 0.75) {
          _currentStageText = "Running AI Analysis...";
        } else {
          _currentStageText = "Generating Report...";
        }
      });
    });
  }

  void _stopProgressSimulation(bool success) {
    _stageTimer?.cancel();
    setState(() {
      _isAnalyzing = false;
      _stageProgress = success ? 1.0 : 0.0;
    });
  }

  Future<void> _uploadAndAnalyzeFile() async {
    if (_selectedPlatformFile == null) return;

    _startProgressSimulation();

    final provider = context.read<DocumentProvider>();
    final docData = await provider.uploadDocument(_selectedPlatformFile!);

    if (!mounted) return;

    if (docData != null) {
      _stopProgressSimulation(true);
      context.read<AuthProvider>().refreshStats();
      context.read<HistoryProvider>().loadHistory(); // Reload history grid

      setState(() {
        _completedDocData = docData;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✓ Analysis Complete!'),
          backgroundColor: Colors.green,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } else {
      _stopProgressSimulation(false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(provider.errorMessage ?? 'Upload failed'),
          backgroundColor: AppColors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  IconData _getFileIcon(String? name) {
    if (name == null) return Icons.insert_drive_file_rounded;
    final ext = name.split('.').last.toLowerCase();
    switch (ext) {
      case 'pdf':
        return Icons.picture_as_pdf_rounded;
      case 'docx':
      case 'doc':
        return Icons.description_rounded;
      case 'txt':
        return Icons.text_snippet_rounded;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'webp':
        return Icons.image_rounded;
      default:
        return Icons.insert_drive_file_rounded;
    }
  }

  Color _getFileColor(String? name) {
    if (name == null) return AppColors.textHint;
    final ext = name.split('.').last.toLowerCase();
    switch (ext) {
      case 'pdf':
        return AppColors.highRisk;
      case 'docx':
      case 'doc':
        return AppColors.info;
      case 'txt':
        return AppColors.textSecondary;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'webp':
        return AppColors.success;
      default:
        return AppColors.gold;
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<DocumentProvider>();
    final history = context.watch<HistoryProvider>();
    final screenWidth = MediaQuery.of(context).size.width;
    final isDesktop = screenWidth >= 950;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    // Center layout structure
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: Navigator.canPop(context)
            ? IconButton(
                icon: Icon(Icons.arrow_back_ios_new_rounded, color: AppColors.textPrimary),
                onPressed: () => Navigator.pop(context),
              )
            : null,
        title: Text(
          'Document Intelligence Center',
          style: GoogleFonts.inter(
            fontSize: 20,
            fontWeight: FontWeight.w800,
            color: AppColors.textPrimary,
          ),
        ),
        centerTitle: true,
      ),
      body: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 1200),
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: isDesktop
                ? Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Left Column: Upload Workstation
                      Expanded(
                        flex: 7,
                        child: _buildUploadWorkstation(provider, isDark),
                      ),
                      const SizedBox(width: 32),
                      // Right Column: Recent Uploads Side-Panel
                      Expanded(
                        flex: 5,
                        child: _buildRecentUploadsPanel(history),
                      ),
                    ],
                  )
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildUploadWorkstation(provider, isDark),
                      const SizedBox(height: 36),
                      _buildRecentUploadsPanel(history),
                    ],
                  ),
          ),
        ),
      ),
    );
  }

  Widget _buildUploadWorkstation(DocumentProvider provider, bool isDark) {
    if (_isAnalyzing) {
      return _buildAnalyzingState();
    }

    if (_completedDocData != null) {
      return _buildSuccessCard();
    }

    if (_selectedPlatformFile != null) {
      return _buildFileSelectedState(isDark);
    }

    return _buildDropZone();
  }

  // 1. Core DropZone Widget
  Widget _buildDropZone() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Upload Document',
          style: GoogleFonts.inter(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 12),
        GestureDetector(
          onTap: _pickFile,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 60, horizontal: 24),
            decoration: BoxDecoration(
              color: AppColors.cardDark,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: AppColors.border,
                width: 2.0,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Animated Cloud Upload Icon
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: AppColors.goldGlow,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.cloud_upload_outlined,
                    size: 56,
                    color: AppColors.gold,
                  ),
                )
                    .animate(onPlay: (controller) => controller.repeat(reverse: true))
                    .slide(begin: const Offset(0, -0.05), end: const Offset(0, 0.05), duration: 1500.ms, curve: Curves.easeInOut),
                const SizedBox(height: 24),
                Text(
                  'Drag and drop your file here, or click browse',
                  style: GoogleFonts.inter(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 8),
                Text(
                  'Maximum size: 20 MB',
                  style: GoogleFonts.inter(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textHint,
                  ),
                ),
                const SizedBox(height: 32),
                ElevatedButton.icon(
                  onPressed: _pickFile,
                  icon: const Icon(Icons.search_rounded, size: 18),
                  label: Text('Browse Files', style: GoogleFonts.inter(fontWeight: FontWeight.w700)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.gold,
                    foregroundColor: AppColors.navy,
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    elevation: 0,
                  ),
                ),
              ],
            ),
          ),
        ).animate().fadeIn(duration: 300.ms),
        const SizedBox(height: 24),
        // Supported Formats Grid/List
        _buildSupportedFormatsSection(),
      ],
    );
  }

  Widget _buildSupportedFormatsSection() {
    final formats = [
      {'label': 'PDF', 'ext': 'pdf', 'icon': Icons.picture_as_pdf_rounded, 'color': AppColors.highRisk},
      {'label': 'DOCX', 'ext': 'docx', 'icon': Icons.description_rounded, 'color': AppColors.info},
      {'label': 'DOC', 'ext': 'doc', 'icon': Icons.article_rounded, 'color': AppColors.info},
      {'label': 'TXT', 'ext': 'txt', 'icon': Icons.text_snippet_rounded, 'color': AppColors.textSecondary},
      {'label': 'PNG', 'ext': 'png', 'icon': Icons.image_rounded, 'color': AppColors.success},
      {'label': 'JPG', 'ext': 'jpg', 'icon': Icons.image_rounded, 'color': AppColors.success},
      {'label': 'JPEG', 'ext': 'jpeg', 'icon': Icons.image_rounded, 'color': AppColors.success},
      {'label': 'WEBP', 'ext': 'webp', 'icon': Icons.image_rounded, 'color': AppColors.success},
    ];

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.cardDark,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Supported Formats',
            style: GoogleFonts.inter(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: formats.map((f) {
              final Color color = f['color'] as Color;
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: color.withValues(alpha: 0.15)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(f['icon'] as IconData, size: 16, color: color),
                    const SizedBox(width: 6),
                    Text(
                      f['label'] as String,
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: color,
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    ).animate().fadeIn(delay: 150.ms);
  }

  // 2. File Selected state with analysis checkboxes
  Widget _buildFileSelectedState(bool isDark) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Selected File',
          style: GoogleFonts.inter(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 12),
        // File Preview Card
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: AppColors.cardDark,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.border, width: 1.5),
          ),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: _getFileColor(_fileName).withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  _getFileIcon(_fileName),
                  color: _getFileColor(_fileName),
                  size: 24,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _fileName ?? 'Unnamed File',
                      style: GoogleFonts.inter(
                        fontSize: 14.5,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textPrimary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _fileSize ?? '',
                      style: GoogleFonts.inter(
                        fontSize: 12.5,
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close_rounded, color: AppColors.error),
                onPressed: _removeSelectedFile,
                tooltip: 'Remove selected file',
              ),
            ],
          ),
        ).animate().scale(curve: Curves.easeOutBack, duration: 300.ms),
        const SizedBox(height: 24),
        // Analysis Options
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: AppColors.cardDark,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.border),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Analysis Orchestration Options',
                style: GoogleFonts.inter(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Select which engines run on this document:',
                style: GoogleFonts.inter(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 16),
              // Checklist
              _buildCheckboxOption('OCR Text Detection', _ocrDetection, (val) => setState(() => _ocrDetection = val ?? true)),
              _buildCheckboxOption('Clause Extraction & Tagging', _clauseExtraction, (val) => setState(() => _clauseExtraction = val ?? true)),
              _buildCheckboxOption('Risk Analysis & Flagging', _riskAnalysis, (val) => setState(() => _riskAnalysis = val ?? true)),
              _buildCheckboxOption('AI Summary & Key Takeaways', _aiSummary, (val) => setState(() => _aiSummary = val ?? true)),
              _buildCheckboxOption('Key Dates & Deadlines Extraction', _keyDates, (val) => setState(() => _keyDates = val ?? true)),
              _buildCheckboxOption('Signing Parties & Entities Detection', _importantParties, (val) => setState(() => _importantParties = val ?? true)),
            ],
          ),
        ).animate().fadeIn(delay: 100.ms),
        const SizedBox(height: 28),
        // Analyze Button
        SizedBox(
          width: double.infinity,
          height: 54,
          child: ElevatedButton.icon(
            onPressed: _uploadAndAnalyzeFile,
            icon: const Icon(Icons.bolt_rounded, size: 20),
            label: Text(
              'Analyze Document',
              style: GoogleFonts.inter(fontSize: 16, fontWeight: FontWeight.w700),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.gold,
              foregroundColor: AppColors.navy,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
              elevation: 0,
            ),
          ),
        ).animate().fadeIn(delay: 200.ms),
      ],
    );
  }

  Widget _buildCheckboxOption(String label, bool value, ValueChanged<bool?> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: CheckboxListTile(
        title: Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: AppColors.textPrimary,
          ),
        ),
        value: value,
        onChanged: onChanged,
        activeColor: AppColors.gold,
        checkColor: AppColors.navy,
        dense: true,
        contentPadding: EdgeInsets.zero,
        controlAffinity: ListTileControlAffinity.leading,
      ),
    );
  }

  // 3. Analyzing state with progressive stages
  Widget _buildAnalyzingState() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(40),
      decoration: BoxDecoration(
        color: AppColors.cardDark,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Breathtaking scanning animation
          Stack(
            alignment: Alignment.center,
            children: [
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  color: AppColors.goldGlow,
                  shape: BoxShape.circle,
                ),
              ).animate(onPlay: (controller) => controller.repeat()).scale(
                    begin: const Offset(1, 1),
                    end: const Offset(1.5, 1.5),
                    duration: 1200.ms,
                    curve: Curves.easeOut,
                  ),
              const Icon(
                Icons.psychology_outlined,
                size: 52,
                color: AppColors.gold,
              ).animate().scale(curve: Curves.elasticOut, duration: 600.ms),
            ],
          ),
          const SizedBox(height: 36),
          // Animated Stage Text
          Text(
            _currentStageText,
            style: GoogleFonts.inter(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: AppColors.textPrimary,
            ),
          ).animate(key: ValueKey(_currentStageText)).fadeIn(duration: 200.ms).scale(begin: const Offset(0.95, 0.95)),
          const SizedBox(height: 18),
          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: SizedBox(
              width: 240,
              height: 6,
              child: LinearProgressIndicator(
                value: _stageProgress,
                backgroundColor: AppColors.border,
                valueColor: const AlwaysStoppedAnimation<Color>(AppColors.gold),
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            '${(_stageProgress * 100).toStringAsFixed(0)}% analyzed',
            style: GoogleFonts.inter(
              fontSize: 12,
              color: AppColors.textHint,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  // 4. Success state card
  Widget _buildSuccessCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(36),
      decoration: BoxDecoration(
        color: AppColors.cardDark,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: const BoxDecoration(
              color: AppColors.successBg,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.check_circle_outline_rounded,
              size: 56,
              color: AppColors.success,
            ),
          ).animate().scale(curve: Curves.elasticOut, duration: 600.ms),
          const SizedBox(height: 24),
          Text(
            'Analysis Complete',
            style: GoogleFonts.inter(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'We successfully extracted text, labeled key clauses, and generated a comprehensive risk assessment for your document.',
            style: GoogleFonts.inter(
              fontSize: 13,
              color: AppColors.textSecondary,
              height: 1.5,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),
          Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 50,
                  child: ElevatedButton(
                    onPressed: () {
                      final docId = _completedDocData?['id'];
                      if (docId != null) {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => AnalysisResultScreen(documentId: docId),
                          ),
                        );
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.gold,
                      foregroundColor: AppColors.navy,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      elevation: 0,
                    ),
                    child: Text(
                      'Open Analysis',
                      style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 14),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: SizedBox(
                  height: 50,
                  child: OutlinedButton(
                    onPressed: _removeSelectedFile,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.textPrimary,
                      side: BorderSide(color: AppColors.border),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: Text(
                      'Upload Another',
                      style: GoogleFonts.inter(fontWeight: FontWeight.w700, fontSize: 14),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    ).animate().fadeIn(duration: 400.ms);
  }

  // 5. Recent Uploads panel (used on right side in desktop layout)
  Widget _buildRecentUploadsPanel(HistoryProvider history) {
    final recentDocs = history.documents;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Recent Uploads',
              style: GoogleFonts.inter(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: AppColors.textPrimary,
              ),
            ),
            if (recentDocs.isNotEmpty)
              Text(
                '${recentDocs.length} total',
                style: GoogleFonts.inter(
                  fontSize: 12.5,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textHint,
                ),
              ),
          ],
        ),
        const SizedBox(height: 12),
        if (history.isLoading)
          const Center(
            child: Padding(
              padding: EdgeInsets.symmetric(vertical: 36),
              child: CircularProgressIndicator(color: AppColors.gold),
            ),
          )
        else if (recentDocs.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(28),
            decoration: BoxDecoration(
              color: AppColors.cardDark,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              children: [
                Icon(Icons.folder_open_rounded, size: 36, color: AppColors.textHint),
                const SizedBox(height: 12),
                Text(
                  'No recent uploads',
                  style: GoogleFonts.inter(
                    fontSize: 13.5,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Upload a legal document to see your history.',
                  style: GoogleFonts.inter(
                    fontSize: 11.5,
                    color: AppColors.textSecondary,
                  ),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          )
        else
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: recentDocs.take(4).length,
            itemBuilder: (context, i) {
              final doc = recentDocs[i];
              return DocumentCard(
                document: doc,
                showDelete: false,
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => AnalysisResultScreen(documentId: doc.id),
                  ),
                ),
              );
            },
          ),
      ],
    );
  }
}
