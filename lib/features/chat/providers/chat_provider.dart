import 'package:flutter/material.dart';
import 'package:lexguard_ai/models/chat_model.dart';
import 'package:lexguard_ai/services/chat_service.dart';
import 'package:uuid/uuid.dart';

class ChatProvider extends ChangeNotifier {
  final ChatService _chatService = ChatService();
  final List<ChatMessage> _messages = [];
  bool _isTyping = false;
  String? _errorMessage;
  String? _currentDocumentId; // null until a document is selected
  String? _currentDocumentName;
  final _uuid = const Uuid();

  List<ChatMessage> get messages => _messages;
  bool get isTyping => _isTyping;
  String? get errorMessage => _errorMessage;
  String? get currentDocumentId => _currentDocumentId;
  String? get currentDocumentName => _currentDocumentName;
  bool get hasDocumentContext => _currentDocumentId != null;

  String _selectedLanguage = "English";
  bool _isVoiceResponseEnabled = false;

  String get selectedLanguage => _selectedLanguage;
  bool get isVoiceResponseEnabled => _isVoiceResponseEnabled;

  void setSelectedLanguage(String lang) {
    _selectedLanguage = lang;
    notifyListeners();
  }

  void setVoiceResponseEnabled(bool val) {
    _isVoiceResponseEnabled = val;
    notifyListeners();
  }

  void setDocumentContext(String documentId, {String? documentName}) {
    _currentDocumentId = documentId;
    _currentDocumentName = documentName;
    _errorMessage = null;
    loadHistory();
  }

  Future<void> loadHistory() async {
    if (_currentDocumentId == null) {
      _errorMessage = null;
      notifyListeners();
      return;
    }

    _isTyping = true;
    _errorMessage = null;
    notifyListeners();
    
    try {
      final history = await _chatService.getChatHistory(_currentDocumentId!);
      _messages.clear();
      _messages.addAll(history);
    } catch (e) {
      debugPrint('ChatProvider: Failed to load chat history: $e');
      _errorMessage = 'Failed to load chat history';
    } finally {
      _isTyping = false;
      notifyListeners();
    }
  }

  Future<void> sendMessage(String content, {Function(String)? onAiResponse}) async {
    if (content.trim().isEmpty) return;

    if (_currentDocumentId == null) {
      _errorMessage = 'Please select a document to chat with first';
      notifyListeners();
      return;
    }

    final userMsg = ChatMessage(
      id: _uuid.v4(),
      content: content,
      sender: MessageSender.user,
      timestamp: DateTime.now(),
    );
    
    _messages.add(userMsg);
    _isTyping = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final aiMsg = await _chatService.sendMessage(
        _currentDocumentId!, 
        content, 
        language: _selectedLanguage,
        isVoice: _isVoiceResponseEnabled,
      );
      _messages.add(aiMsg);
      _errorMessage = null;
      if (onAiResponse != null) {
        onAiResponse(aiMsg.content);
      }
    } catch (e) {
      debugPrint('ChatProvider: AI chat error: $e');
      _errorMessage = 'AI service is temporarily unavailable';
      _messages.add(ChatMessage(
        id: _uuid.v4(),
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        sender: MessageSender.ai,
        timestamp: DateTime.now(),
      ));
    } finally {
      _isTyping = false;
      notifyListeners();
    }
  }

  Future<void> clearChat() async {
    if (_currentDocumentId != null) {
      await _chatService.clearHistory(_currentDocumentId!);
    }
    _messages.clear();
    _errorMessage = null;
    notifyListeners();
  }
}

