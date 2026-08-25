import 'dart:async';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:lexguard_ai/services/document_service.dart';

class DocumentProvider extends ChangeNotifier {
  final DocumentService _service = DocumentService();

  List<Map<String, dynamic>> _documents = [];
  bool _isDisposed = false;
  final List<Timer> _activeTimers = [];

  @override
  void dispose() {
    _isDisposed = true;
    for (final t in _activeTimers) {
      t.cancel();
    }
    _activeTimers.clear();
    super.dispose();
  }

  @override
  void notifyListeners() {
    if (!_isDisposed) {
      super.notifyListeners();
    }
  }
  Map<String, dynamic>? _currentDocument;
  Map<String, dynamic>? _currentAnalysis;
  List<Map<String, dynamic>> _currentClauses = [];
  List<Map<String, dynamic>> _chatMessages = [];

  bool _isLoading = false;
  bool _isUploading = false;
  bool _isChatting = false;
  String? _errorMessage;
  String? _uploadingDocId;

  // Getters
  List<Map<String, dynamic>> get documents => _documents;
  Map<String, dynamic>? get currentDocument => _currentDocument;
  Map<String, dynamic>? get currentAnalysis => _currentAnalysis;
  List<Map<String, dynamic>> get currentClauses => _currentClauses;
  List<Map<String, dynamic>> get chatMessages => _chatMessages;
  bool get isLoading => _isLoading;
  bool get isUploading => _isUploading;
  bool get isChatting => _isChatting;
  String? get errorMessage => _errorMessage;
  String? get uploadingDocId => _uploadingDocId;

  /// Upload a document and await its complete analysis status (completed / failed)
  Future<Map<String, dynamic>?> uploadAndAwaitAnalysis(
    PlatformFile file, {
    void Function(String status, String stageText, double progress)? onStageChange,
  }) async {
    _isUploading = true;
    _errorMessage = null;
    notifyListeners();

    onStageChange?.call('uploading', 'Uploading document...', 0.15);

    try {
      final result = await _service.uploadDocument(file);
      if (!result['success']) {
        _errorMessage = result['message'] ?? 'Upload failed';
        _isUploading = false;
        notifyListeners();
        return null;
      }

      final docData = result['data']['document'];
      final docId = docData['id'] as String;
      _uploadingDocId = docId;
      _documents.insert(0, docData);
      notifyListeners();

      onStageChange?.call('extracting', 'Preparing image & extracting text...', 0.35);

      // Poll until completed or failed (timeout after 60s max)
      final completer = Completer<Map<String, dynamic>?>();
      int pollCount = 0;

      late Timer timer;
      timer = Timer.periodic(const Duration(seconds: 2), (t) async {
        pollCount++;
        if (_isDisposed) {
          t.cancel();
          _activeTimers.remove(t);
          if (!completer.isCompleted) completer.complete(null);
          return;
        }

        final statusRes = await _service.getDocumentStatus(docId);
        if (_isDisposed) {
          t.cancel();
          _activeTimers.remove(t);
          if (!completer.isCompleted) completer.complete(null);
          return;
        }

        if (statusRes['success']) {
          final status = statusRes['data']['status'] as String? ?? 'pending';
          final errorMsg = statusRes['data']['error_message'] as String?;

          // Update document state in local list
          final idx = _documents.indexWhere((d) => d['id'] == docId);
          if (idx != -1) {
            _documents[idx]['status'] = status;
            _documents[idx]['risk_score'] = statusRes['data']['risk_score'];
            _documents[idx]['risk_level'] = statusRes['data']['risk_level'];
            _documents[idx]['error_message'] = errorMsg;
            notifyListeners();
          }

          if (status == 'extracting') {
            onStageChange?.call('extracting', 'Preparing image & extracting text...', 0.45);
          } else if (status == 'analyzing') {
            onStageChange?.call('analyzing', 'Analyzing legal content with AI...', 0.75);
          } else if (status == 'completed') {
            onStageChange?.call('completed', 'Analysis complete', 1.0);
            t.cancel();
            _activeTimers.remove(t);
            _uploadingDocId = null;
            _isUploading = false;
            await fetchDocuments();
            
            // Get full detail
            final detailRes = await _service.getDocumentDetail(docId);
            final fullDoc = detailRes['success'] ? detailRes['data']['document'] : docData;
            if (!completer.isCompleted) completer.complete(fullDoc);
            return;
          } else if (status == 'failed') {
            onStageChange?.call('failed', 'Analysis failed', 0.0);
            t.cancel();
            _activeTimers.remove(t);
            _uploadingDocId = null;
            _isUploading = false;
            _errorMessage = errorMsg ?? 'Document analysis failed';
            notifyListeners();
            if (!completer.isCompleted) completer.complete(null);
            return;
          }
        }

        if (pollCount > 30) { // 60s timeout limit
          t.cancel();
          _activeTimers.remove(t);
          _uploadingDocId = null;
          _isUploading = false;
          _errorMessage = 'Analysis polling timed out';
          notifyListeners();
          if (!completer.isCompleted) completer.complete(null);
        }
      });

      _activeTimers.add(timer);
      return await completer.future;

    } catch (e) {
      _errorMessage = 'Upload failed: $e';
      _isUploading = false;
      notifyListeners();
      return null;
    }
  }

  /// Fetch all documents
  Future<void> fetchDocuments() async {
    _isLoading = true;
    notifyListeners();

    final result = await _service.getDocuments();
    if (result['success']) {
      _documents = List<Map<String, dynamic>>.from(
        result['data']['documents'] ?? [],
      );
    } else {
      _errorMessage = result['message'];
    }
    _isLoading = false;
    notifyListeners();
  }

  /// Fetch document details with analysis
  Future<void> fetchDocumentDetail(String documentId) async {
    // Purge previous state to prevent cross-document data leakage
    _currentDocument = null;
    _currentAnalysis = null;
    _currentClauses = [];
    _chatMessages = [];
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    final result = await _service.getDocumentDetail(documentId);
    if (result['success']) {
      _currentDocument = result['data']['document'];
      _currentAnalysis = result['data']['analysis'];
      _currentClauses = List<Map<String, dynamic>>.from(
        result['data']['clauses'] ?? [],
      );
    } else {
      _errorMessage = result['message'];
    }
    _isLoading = false;
    notifyListeners();
  }

  /// Send a chat message about a document
  Future<String?> sendChatMessage(String documentId, String query) async {
    _isChatting = true;
    notifyListeners();

    // Add user message immediately
    _chatMessages.add({
      'role': 'user',
      'content': query,
      'timestamp': DateTime.now().toIso8601String(),
    });
    notifyListeners();

    final result = await _service.chatWithDocument(documentId, query);
    if (result['success']) {
      final answer = result['data']['answer'];
      _chatMessages.add({
        'role': 'assistant',
        'content': answer,
        'timestamp': DateTime.now().toIso8601String(),
      });
      _isChatting = false;
      notifyListeners();
      return answer;
    } else {
      final errDetail = result['message'] ?? 'Unable to generate response. Please try again.';
      _chatMessages.add({
        'role': 'assistant',
        'content': errDetail,
        'timestamp': DateTime.now().toIso8601String(),
      });
      _isChatting = false;
      notifyListeners();
      return null;
    }
  }

  /// Load chat history for a document
  Future<void> loadChatHistory(String documentId) async {
    final result = await _service.getChatHistory(documentId);
    if (result['success']) {
      _chatMessages = [];
      final history = result['data']['history'] ?? [];
      for (var chat in history) {
        // Backend returns {id, query, response, created_at}
        _chatMessages.add({
          'role': 'user',
          'content': chat['query'],
          'timestamp': chat['created_at'],
        });
        _chatMessages.add({
          'role': 'assistant',
          'content': chat['response'],
          'timestamp': chat['created_at'],
        });
      }
      notifyListeners();
    }
  }

  /// Clear chat messages
  void clearChat() {
    _chatMessages = [];
    notifyListeners();
  }

  /// Delete a document
  Future<bool> deleteDocument(String documentId) async {
    final result = await _service.deleteDocument(documentId);
    if (result['success']) {
      _documents.removeWhere((d) => d['id'] == documentId);
      notifyListeners();
      return true;
    }
    return false;
  }

  /// Get export report URL for a document
  String getExportUrl(String documentId) {
    return '${_service.getBaseUrl()}/documents/$documentId/export';
  }

  /// Clear current document
  void clearCurrentDocument() {
    _currentDocument = null;
    _currentAnalysis = null;
    _currentClauses = [];
    _chatMessages = [];
    notifyListeners();
  }
}
