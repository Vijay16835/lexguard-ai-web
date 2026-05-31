import 'document_model.dart';

class AnalysisModel {
  final String id;
  final String documentId;
  final String documentName;
  final String summary;
  final int riskScore;
  final RiskLevel riskLevel;
  final double aiConfidence;
  final List<KeyClause> keyClauses;
  final List<ImportantDate> importantDates;
  final List<Party> parties;
  final List<String> obligations;
  final List<String> recommendations;
  final DateTime analyzedAt;

  AnalysisModel({
    required this.id,
    required this.documentId,
    required this.documentName,
    required this.summary,
    required this.riskScore,
    required this.riskLevel,
    required this.aiConfidence,
    required this.keyClauses,
    required this.importantDates,
    required this.parties,
    required this.obligations,
    required this.recommendations,
    required this.analyzedAt,
  });

  static AnalysisModel get dummy => AnalysisModel(
    id: 'an_1',
    documentId: 'doc_1',
    documentName: 'Service_Agreement_v4.pdf',
    summary: 'This is a standard service agreement outlining software development deliverables, timeline, intellectual property transfers, and liabilities.',
    riskScore: 35,
    riskLevel: RiskLevel.low,
    aiConfidence: 0.92,
    keyClauses: [
      KeyClause(
        title: 'Intellectual Property Assignment',
        content: 'All Intellectual Property Rights in works generated under this Agreement shall vest in the Customer upon receipt of full payment.',
        risk: RiskLevel.low,
        summary: 'Low risk. Rights transfer is standard but contingent on payment completion.',
      ),
      KeyClause(
        title: 'Limitation of Liability',
        content: 'Neither party shall be liable for indirect, incidental, or consequential damages. Maximum aggregate liability is capped at 100% of fees paid.',
        risk: RiskLevel.medium,
        summary: 'Standard liability cap, protecting both vendor and client.',
      ),
    ],
    importantDates: [
      ImportantDate(label: 'Effective Date', date: DateTime.now(), description: 'Start of project engagement'),
    ],
    parties: [
      Party(name: 'DevCorp Inc.', role: 'Service Provider', jurisdiction: 'Delaware'),
      Party(name: 'ClientTech LLC', role: 'Customer', jurisdiction: 'Delaware'),
    ],
    obligations: [
      'Provide weekly status updates',
      'Provide access to sandbox hosting environments',
    ],
    recommendations: [
      'Verify that payment milestones align with actual project phases',
    ],
    analyzedAt: DateTime.now(),
  );
}

class KeyClause {
  final String title;
  final String content;
  final RiskLevel risk;
  final String summary;

  KeyClause({
    required this.title,
    required this.content,
    required this.risk,
    required this.summary,
  });
}

class ImportantDate {
  final String label;
  final DateTime date;
  final String description;

  ImportantDate({
    required this.label,
    required this.date,
    required this.description,
  });
}

class Party {
  final String name;
  final String role;
  final String jurisdiction;

  Party({required this.name, required this.role, required this.jurisdiction});
}
