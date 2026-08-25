import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:lexguard_ai/core/theme/app_colors.dart';
import 'package:lexguard_ai/models/document_model.dart';
import 'package:intl/intl.dart';

class DocumentCard extends StatefulWidget {
  final DocumentModel document;
  final VoidCallback? onTap;
  final VoidCallback? onDelete;
  final VoidCallback? onMore;
  final bool showDelete;

  const DocumentCard({
    super.key,
    required this.document,
    this.onTap,
    this.onDelete,
    this.onMore,
    this.showDelete = false,
  });

  @override
  State<DocumentCard> createState() => _DocumentCardState();
}

class _DocumentCardState extends State<DocumentCard> {
  bool _isHovered = false;

  Color get _riskColor {
    switch (widget.document.riskLevel) {
      case RiskLevel.high:
        return AppColors.highRisk;
      case RiskLevel.medium:
        return AppColors.warning;
      case RiskLevel.low:
        return AppColors.success;
      default:
        return AppColors.textHint;
    }
  }

  Color get _statusColor {
    switch (widget.document.status) {
      case DocumentStatus.completed:
        return AppColors.success;
      case DocumentStatus.analyzing:
        return AppColors.warning;
      case DocumentStatus.failed:
        return AppColors.error;
      default:
        return AppColors.textHint;
    }
  }

  IconData get _fileIcon {
    switch (widget.document.type) {
      case DocumentType.pdf:
        return Icons.picture_as_pdf_rounded;
      case DocumentType.docx:
        return Icons.description_rounded;
      case DocumentType.image:
        return Icons.image_rounded;
      default:
        return Icons.insert_drive_file_rounded;
    }
  }

  Color get _fileIconColor {
    switch (widget.document.type) {
      case DocumentType.pdf:
        return AppColors.highRisk;
      case DocumentType.docx:
        return AppColors.info;
      case DocumentType.image:
        return AppColors.success;
      default:
        return AppColors.textHint;
    }
  }

  @override
  Widget build(BuildContext context) {
    final String formattedDate = DateFormat('MMM d, yyyy • h:mm a').format(widget.document.uploadedAt);
    final hasSummary = widget.document.summary != null && widget.document.summary!.isNotEmpty;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeInOut,
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          color: _isHovered
              ? (isDark ? const Color(0xFF162544) : const Color(0xFFEDF2FA))
              : AppColors.cardDark,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: _isHovered ? AppColors.gold.withValues(alpha: 0.5) : AppColors.border,
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: _isHovered
                  ? AppColors.gold.withValues(alpha: 0.08)
                  : Colors.black.withValues(alpha: 0.03),
              blurRadius: _isHovered ? 16 : 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: InkWell(
          onTap: widget.onTap,
          borderRadius: BorderRadius.circular(18),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Upper Section: Icon, Name, Badges
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // File Icon with background glow
                    Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: _fileIconColor.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(14),
                      ),
                      child: Icon(_fileIcon, color: _fileIconColor, size: 28),
                    ),
                    const SizedBox(width: 14),
                    // Document Name, Size, Upload Time
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.document.name,
                            style: GoogleFonts.inter(
                              fontSize: 15,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textPrimary,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              Icon(Icons.access_time_rounded, size: 12, color: AppColors.textHint),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Text(
                                  formattedDate,
                                  style: GoogleFonts.inter(
                                    fontSize: 12,
                                    color: AppColors.textSecondary,
                                    fontWeight: FontWeight.w500,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Container(
                                width: 4,
                                height: 4,
                                decoration: BoxDecoration(
                                  color: AppColors.textHint,
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                '${widget.document.sizeInMB.toStringAsFixed(2)} MB',
                                style: GoogleFonts.inter(
                                  fontSize: 12,
                                  color: AppColors.textSecondary,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    if (widget.onMore != null) ...[
                      const SizedBox(width: 8),
                      IconButton(
                        icon: const Icon(Icons.more_vert_rounded),
                        onPressed: widget.onMore,
                        color: AppColors.textHint,
                        tooltip: 'More actions',
                        splashRadius: 20,
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 14),
                // Badges Section
                Row(
                  children: [
                    // Status Badge (Completed/Analyzing/Failed)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: _statusColor.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: _statusColor.withValues(alpha: 0.2)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 6,
                            height: 6,
                            decoration: BoxDecoration(
                              color: _statusColor,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            widget.document.statusLabel,
                            style: GoogleFonts.inter(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: _statusColor,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    // Risk Badge
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: _riskColor.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: _riskColor.withValues(alpha: 0.2)),
                      ),
                      child: Text(
                        widget.document.riskLabel,
                        style: GoogleFonts.inter(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: _riskColor,
                        ),
                      ),
                    ),
                    if (widget.document.documentCategory != null && widget.document.documentCategory!.isNotEmpty) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.gold.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: AppColors.gold.withValues(alpha: 0.2)),
                        ),
                        child: Text(
                          widget.document.documentCategory!,
                          style: GoogleFonts.inter(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: AppColors.gold,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 12),
                // Summary Preview (Max 2 lines)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: isDark ? const Color(0xFF0D1F3C) : const Color(0xFFF8FAFC),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    hasSummary
                        ? widget.document.summary!
                        : (widget.document.status == DocumentStatus.analyzing
                            ? "AI Analysis in progress. Extracting key terms, clauses, and risk factors..."
                            : "No summary preview available for this document."),
                    style: GoogleFonts.inter(
                      fontSize: 12.5,
                      color: hasSummary ? AppColors.textPrimary : AppColors.textSecondary,
                      height: 1.5,
                      fontStyle: hasSummary ? FontStyle.normal : FontStyle.italic,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(height: 14),
                // Action Buttons: Open & Delete
                const Divider(height: 1),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Open Button
                    ElevatedButton.icon(
                      onPressed: widget.onTap,
                      icon: const Icon(Icons.folder_open_rounded, size: 16),
                      label: Text(
                        'Open Analysis',
                        style: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 13),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.gold,
                        foregroundColor: AppColors.navy,
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                        elevation: 0,
                      ),
                    ),
                    // Delete Button
                    if (widget.showDelete && widget.onDelete != null)
                      TextButton.icon(
                        onPressed: widget.onDelete,
                        icon: const Icon(Icons.delete_outline_rounded, size: 16, color: AppColors.error),
                        label: Text(
                          'Delete',
                          style: GoogleFonts.inter(
                            color: AppColors.error,
                            fontWeight: FontWeight.w600,
                            fontSize: 13,
                          ),
                        ),
                        style: TextButton.styleFrom(
                          foregroundColor: AppColors.error,
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
