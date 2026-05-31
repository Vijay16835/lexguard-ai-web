import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/models/document_model.dart';
import 'package:intl/intl.dart';

class DocumentCard extends StatelessWidget {
  final DocumentModel document;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;
  final bool showDelete;

  const DocumentCard({
    super.key,
    required this.document,
    this.onTap,
    this.onDelete,
    this.showDelete = false,
  });

  Color get _riskColor {
    switch (document.riskLevel) {
      case RiskLevel.high: return AppColors.highRisk;
      case RiskLevel.medium: return AppColors.mediumRisk;
      case RiskLevel.low: return AppColors.lowRisk;
      default: return AppColors.textHint;
    }
  }

  Color get _statusColor {
    switch (document.status) {
      case DocumentStatus.completed: return AppColors.success;
      case DocumentStatus.analyzing: return AppColors.warning;
      case DocumentStatus.failed: return AppColors.error;
      default: return AppColors.textHint;
    }
  }

  IconData get _fileIcon {
    switch (document.type) {
      case DocumentType.pdf: return Icons.picture_as_pdf_outlined;
      case DocumentType.docx: return Icons.description_outlined;
      case DocumentType.image: return Icons.image_outlined;
      default: return Icons.insert_drive_file_outlined;
    }
  }

  Color get _fileIconColor {
    switch (document.type) {
      case DocumentType.pdf: return AppColors.highRisk;
      case DocumentType.docx: return AppColors.info;
      case DocumentType.image: return AppColors.success;
      default: return AppColors.textHint;
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.cardDark,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(children: [
          // File Icon
          Container(
            width: 46, height: 46,
            decoration: BoxDecoration(color: _fileIconColor.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12)),
            child: Icon(_fileIcon, color: _fileIconColor, size: 24),
          ),
          const SizedBox(width: 12),
          // Info
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(document.name, style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary), maxLines: 1, overflow: TextOverflow.ellipsis),
              const SizedBox(height: 4),
              Row(children: [
                Text(DateFormat('MMM d, yyyy').format(document.uploadedAt), style: GoogleFonts.inter(fontSize: 11, color: AppColors.textHint)),
                const SizedBox(width: 8),
                Text('•', style: GoogleFonts.inter(color: AppColors.textHint, fontSize: 11)),
                const SizedBox(width: 8),
                Text('${document.sizeInMB} MB', style: GoogleFonts.inter(fontSize: 11, color: AppColors.textHint)),
              ]),
              const SizedBox(height: 6),
              Row(children: [
                // Status Badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(color: _statusColor.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(6)),
                  child: Text(document.statusLabel, style: GoogleFonts.inter(fontSize: 10, fontWeight: FontWeight.w700, color: _statusColor)),
                ),
                if (document.riskLevel != null) ...[
                  const SizedBox(width: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(color: _riskColor.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(6)),
                    child: Text(document.riskLabel, style: GoogleFonts.inter(fontSize: 10, fontWeight: FontWeight.w700, color: _riskColor)),
                  ),
                ],
              ]),
            ]),
          ),
          // Actions
          Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            if (showDelete && onDelete != null)
              GestureDetector(
                onTap: onDelete,
                child: Container(
                  padding: const EdgeInsets.all(6),
                  decoration: BoxDecoration(color: AppColors.errorBg, borderRadius: BorderRadius.circular(8)),
                  child: const Icon(Icons.delete_outline_rounded, size: 16, color: AppColors.error),
                ),
              ),
            if (onTap != null) ...[
              const SizedBox(height: 6),
              Icon(Icons.chevron_right, color: AppColors.textHint, size: 20),
            ],
          ]),
        ]),
      ),
    );
  }
}
