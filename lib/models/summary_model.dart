class SummaryModel {
  final String id;
  final String documentId;
  final String shortSummary;
  final List<String> keyClauses;
  final List<String> importantDates;
  final List<String> partiesInvolved;
  final List<String> obligations;
  final List<String> recommendations;
  final DateTime generatedAt;

  SummaryModel({
    required this.id,
    required this.documentId,
    required this.shortSummary,
    required this.keyClauses,
    required this.importantDates,
    required this.partiesInvolved,
    required this.obligations,
    required this.recommendations,
    required this.generatedAt,
  });

  factory SummaryModel.fromJson(Map<String, dynamic> json) {
    return SummaryModel(
      id: json['id'],
      documentId: json['documentId'],
      shortSummary: json['shortSummary'],
      keyClauses: List<String>.from(json['keyClauses'] ?? []),
      importantDates: List<String>.from(json['importantDates'] ?? []),
      partiesInvolved: List<String>.from(json['partiesInvolved'] ?? []),
      obligations: List<String>.from(json['obligations'] ?? []),
      recommendations: List<String>.from(json['recommendations'] ?? []),
      generatedAt: DateTime.parse(json['generatedAt']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'documentId': documentId,
      'shortSummary': shortSummary,
      'keyClauses': keyClauses,
      'importantDates': importantDates,
      'partiesInvolved': partiesInvolved,
      'obligations': obligations,
      'recommendations': recommendations,
      'generatedAt': generatedAt.toIso8601String(),
    };
  }
}
