import 'package:flutter/material.dart';
import 'package:lexguard_ai/models/document_model.dart';
import 'package:lexguard_ai/models/summary_model.dart';
import 'package:lexguard_ai/services/chat_service.dart';
import 'package:lexguard_ai/services/document_service.dart';

enum SummaryState { idle, processing, success, error }

class SummaryProvider extends ChangeNotifier {
  final ChatService _chatService = ChatService();
  final DocumentService _docService = DocumentService();

  SummaryState _state = SummaryState.idle;
  SummaryModel? _summary;
  String? _errorMessage;
  String _selectedLanguage = "English";

  SummaryState get state => _state;
  SummaryModel? get summary => _summary;
  String? get errorMessage => _errorMessage;
  String get selectedLanguage => _selectedLanguage;

  bool _isDisposed = false;

  @override
  void dispose() {
    _isDisposed = true;
    super.dispose();
  }

  @override
  void notifyListeners() {
    if (!_isDisposed) {
      super.notifyListeners();
    }
  }

  void clearSummary() {
    _state = SummaryState.idle;
    _summary = null;
    _errorMessage = null;
    _selectedLanguage = "English";
    notifyListeners();
  }

  Future<void> translateSummary(String lang) async {
    if (_summary == null) return;
    _state = SummaryState.processing;
    _selectedLanguage = lang;
    _errorMessage = null;
    notifyListeners();

    try {
      final audioSummaryData = await _chatService.getAudioSummary(_summary!.documentId, language: lang);
      final translatedSummaryText = audioSummaryData['summary_text'] ?? _summary!.shortSummary;
      
      _summary = SummaryModel(
        id: _summary!.id,
        documentId: _summary!.documentId,
        shortSummary: translatedSummaryText,
        keyClauses: _summary!.keyClauses,
        importantDates: _summary!.importantDates,
        partiesInvolved: _summary!.partiesInvolved,
        obligations: _summary!.obligations,
        recommendations: _summary!.recommendations,
        generatedAt: _summary!.generatedAt,
      );
      _state = SummaryState.success;
      notifyListeners();
    } catch (e) {
      _state = SummaryState.error;
      _errorMessage = 'Failed to translate summary: $e';
      notifyListeners();
    }
  }

  Future<void> generateSummary(DocumentModel document) async {
    _state = SummaryState.processing;
    _errorMessage = null;
    _selectedLanguage = "English";
    notifyListeners();

    try {
      final res = await _docService.getSummary(document.id);
      if (res['success'] == true && res['data'] != null) {
        final summaryObj = res['data']['summary'] ?? res['data'];
        final String shortSum = summaryObj['short_summary'] ?? summaryObj['summary'] ?? document.summary ?? 'Summary generated successfully.';
        
        List<String> keyClauses = [];
        if (summaryObj['important_clauses'] != null) {
          keyClauses = List<String>.from(summaryObj['important_clauses']);
        } else if (summaryObj['key_points'] != null) {
          keyClauses = List<String>.from(summaryObj['key_points']);
        }

        List<String> importantDates = summaryObj['important_dates'] != null ? List<String>.from(summaryObj['important_dates']) : [];
        List<String> partiesInvolved = summaryObj['parties'] != null ? List<String>.from(summaryObj['parties']) : [];
        List<String> obligations = summaryObj['obligations'] != null ? List<String>.from(summaryObj['obligations']) : [];
        List<String> recommendations = summaryObj['recommendations'] != null ? List<String>.from(summaryObj['recommendations']) : [];

        _summary = SummaryModel(
          id: 'sum_${document.id}_${DateTime.now().millisecondsSinceEpoch}',
          documentId: document.id,
          shortSummary: shortSum,
          keyClauses: keyClauses.isNotEmpty ? keyClauses : ['Processed document contents.'],
          importantDates: importantDates,
          partiesInvolved: partiesInvolved,
          obligations: obligations,
          recommendations: recommendations,
          generatedAt: DateTime.now(),
        );
        _state = SummaryState.success;
        notifyListeners();
        return;
      }
    } catch (e) {
      debugPrint('SummaryProvider: Backend getSummary failed, checking local document summary: $e');
    }

    if (document.summary != null && document.summary!.isNotEmpty) {
      _summary = SummaryModel(
        id: 'sum_${document.id}_${DateTime.now().millisecondsSinceEpoch}',
        documentId: document.id,
        shortSummary: document.summary!,
        keyClauses: ['Extracted summary preview from document analysis.'],
        importantDates: [],
        partiesInvolved: [],
        obligations: [],
        recommendations: [],
        generatedAt: DateTime.now(),
      );
      _state = SummaryState.success;
      notifyListeners();
    } else {
      _state = SummaryState.error;
      _errorMessage = 'Unable to generate summary for this document. Please try again.';
      notifyListeners();
    }
  }
}
