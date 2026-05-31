import 'package:flutter/material.dart';

enum RiskLevel { low, medium, high }

enum DocumentStatus { pending, analyzing, completed, failed }

enum DocumentType { pdf, docx, image, unknown }

class DocumentModel {
  final String id;
  final String name;
  final String path;
  final DocumentType type;
  final double sizeInMB;
  final DateTime uploadedAt;
  final DocumentStatus status;
  final RiskLevel? riskLevel;
  final int? riskScore;
  final String? summary;
  final String? thumbnailPath;

  DocumentModel({
    required this.id,
    required this.name,
    required this.path,
    required this.type,
    required this.sizeInMB,
    required this.uploadedAt,
    this.status = DocumentStatus.pending,
    this.riskLevel,
    this.riskScore,
    this.summary,
    this.thumbnailPath,
  });

  Color get riskColor {
    switch (riskLevel) {
      case RiskLevel.low:
        return const Color(0xFF2ECC71);
      case RiskLevel.medium:
        return const Color(0xFFF39C12);
      case RiskLevel.high:
        return const Color(0xFFE74C3C);
      default:
        return const Color(0xFF8BA3CC);
    }
  }

  String get riskLabel {
    switch (riskLevel) {
      case RiskLevel.low:
        return 'Low Risk';
      case RiskLevel.medium:
        return 'Medium Risk';
      case RiskLevel.high:
        return 'High Risk';
      default:
        return 'Pending';
    }
  }

  String get typeLabel {
    switch (type) {
      case DocumentType.pdf:
        return 'PDF';
      case DocumentType.docx:
        return 'DOCX';
      case DocumentType.image:
        return 'Image';
      default:
        return 'Unknown';
    }
  }

  String get statusLabel {
    switch (status) {
      case DocumentStatus.pending:
        return 'Pending';
      case DocumentStatus.analyzing:
        return 'Analyzing';
      case DocumentStatus.completed:
        return 'Completed';
      case DocumentStatus.failed:
        return 'Failed';
    }
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'path': path,
      'type': type.index,
      'sizeInMB': sizeInMB,
      'uploadedAt': uploadedAt.toIso8601String(),
      'status': status.index,
      'riskLevel': riskLevel?.index,
      'riskScore': riskScore,
      'summary': summary,
      'thumbnailPath': thumbnailPath,
    };
  }

  static DocumentType _parseDocumentType(dynamic val) {
    if (val == null) return DocumentType.unknown;
    if (val is int) {
      if (val >= 0 && val < DocumentType.values.length) {
        return DocumentType.values[val];
      }
      return DocumentType.unknown;
    }
    final str = val.toString().toLowerCase();
    if (str.contains('pdf')) return DocumentType.pdf;
    if (str.contains('docx') || str.contains('doc')) return DocumentType.docx;
    if (str.contains('jpg') || str.contains('jpeg') || str.contains('png') || str.contains('image')) return DocumentType.image;
    return DocumentType.unknown;
  }

  static DocumentStatus _parseDocumentStatus(dynamic val) {
    if (val == null) return DocumentStatus.pending;
    if (val is int) {
      if (val >= 0 && val < DocumentStatus.values.length) {
        return DocumentStatus.values[val];
      }
      return DocumentStatus.pending;
    }
    final str = val.toString().toLowerCase();
    if (str == 'pending') return DocumentStatus.pending;
    if (str == 'extracting' || str == 'analyzing') return DocumentStatus.analyzing;
    if (str == 'completed') return DocumentStatus.completed;
    if (str == 'failed') return DocumentStatus.failed;
    return DocumentStatus.pending;
  }

  static RiskLevel? _parseRiskLevel(dynamic val) {
    if (val == null) return null;
    if (val is int) {
      if (val >= 0 && val < RiskLevel.values.length) {
        return RiskLevel.values[val];
      }
      return null;
    }
    final str = val.toString().toLowerCase();
    if (str == 'low') return RiskLevel.low;
    if (str == 'medium') return RiskLevel.medium;
    if (str == 'high') return RiskLevel.high;
    return null;
  }

  factory DocumentModel.fromJson(Map<String, dynamic> json) {
    return DocumentModel(
      id: json['id'] ?? '',
      name: json['name'] ?? 'Unnamed Document',
      path: json['path'] ?? '',
      type: _parseDocumentType(json['type']),
      sizeInMB: ((json['size_mb'] ?? json['sizeInMB'] ?? 0.0) as num).toDouble(),
      uploadedAt: DateTime.parse(json['uploaded_at'] ?? json['uploadedAt'] ?? DateTime.now().toIso8601String()),
      status: _parseDocumentStatus(json['status']),
      riskLevel: _parseRiskLevel(json['risk_level'] ?? json['riskLevel']),
      riskScore: json['risk_score'] ?? json['riskScore'],
      summary: json['summary'],
      thumbnailPath: json['thumbnailPath'],
    );
  }

  DocumentModel copyWith({
    String? id,
    String? name,
    String? path,
    DocumentType? type,
    double? sizeInMB,
    DateTime? uploadedAt,
    DocumentStatus? status,
    RiskLevel? riskLevel,
    int? riskScore,
    String? summary,
    String? thumbnailPath,
  }) {
    return DocumentModel(
      id: id ?? this.id,
      name: name ?? this.name,
      path: path ?? this.path,
      type: type ?? this.type,
      sizeInMB: sizeInMB ?? this.sizeInMB,
      uploadedAt: uploadedAt ?? this.uploadedAt,
      status: status ?? this.status,
      riskLevel: riskLevel ?? this.riskLevel,
      riskScore: riskScore ?? this.riskScore,
      summary: summary ?? this.summary,
      thumbnailPath: thumbnailPath ?? this.thumbnailPath,
    );
  }

  static List<DocumentModel> get dummyDocuments => [
    DocumentModel(
      id: 'doc_1',
      name: 'Service_Agreement_v4.pdf',
      path: '/documents/doc_1.pdf',
      type: DocumentType.pdf,
      sizeInMB: 2.4,
      uploadedAt: DateTime.now().subtract(const Duration(days: 2)),
      status: DocumentStatus.completed,
      riskLevel: RiskLevel.low,
      riskScore: 35,
      summary: 'This is a standard service agreement outlining software development deliverables, timeline, intellectual property transfers, and liabilities.',
    ),
    DocumentModel(
      id: 'doc_2',
      name: 'Employment_Contract_Draft.docx',
      path: '/documents/doc_2.docx',
      type: DocumentType.docx,
      sizeInMB: 1.1,
      uploadedAt: DateTime.now().subtract(const Duration(days: 5)),
      status: DocumentStatus.completed,
      riskLevel: RiskLevel.medium,
      riskScore: 55,
      summary: 'Employment agreement draft including non-compete clauses, salary structures, and intellectual property transfers.',
    ),
  ];
}
