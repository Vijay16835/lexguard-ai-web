import 'document_model.dart';

class ClauseModel {
  final String id;
  final String title;
  final String category;
  final String content;
  final String summary;
  final RiskLevel risk;
  final List<String> keywords;
  final String explanation;

  ClauseModel({
    required this.id,
    required this.title,
    required this.category,
    required this.content,
    required this.summary,
    required this.risk,
    required this.keywords,
    required this.explanation,
  });

  static List<ClauseModel> get dummyClauses => [
    ClauseModel(
      id: 'c1',
      title: 'Intellectual Property Assignment',
      category: 'Intellectual Property',
      content: 'All Intellectual Property Rights in works generated under this Agreement shall vest in the Customer upon receipt of full payment.',
      summary: 'Rights transfer to Customer upon full payment.',
      risk: RiskLevel.low,
      keywords: ['Intellectual Property', 'Assignment', 'Work Product'],
      explanation: 'This is standard and low risk because it protects the provider until payment is received, while guaranteeing assignment to the customer after payment.',
    ),
  ];
}
