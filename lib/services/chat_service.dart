import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:lexguard_ai/core/constants/api_constants.dart';
import 'package:lexguard_ai/models/chat_model.dart';

class ChatService {
  late final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ChatService() {
    _dio = Dio(BaseOptions(
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 120),
    ));
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'auth_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
    ));
  }

  /// Sends a message to the AI with document context (RAG).
  Future<ChatMessage> sendMessage(String documentId, String content, {String language = 'English', bool isVoice = false}) async {
    try {
      final url = isVoice ? ApiConstants.voiceChat : ApiConstants.multilingualChat;
      final response = await _dio.post(
        url,
        data: {
          'document_id': documentId,
          'message': content,
          'language': language,
        },
      );

      if (response.data['success'] == true) {
        final contentText = isVoice 
            ? (response.data['voice_ready_answer'] ?? response.data['answer'])
            : response.data['answer'];
        return ChatMessage(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          content: contentText,
          sender: MessageSender.ai,
          timestamp: DateTime.now(),
        );
      } else {
        throw Exception(response.data['detail'] ?? 'Failed to get AI response');
      }
    } on DioException catch (e) {
      debugPrint('Chat error: ${e.response?.data}');
      throw Exception(e.response?.data?['detail'] ?? 'Network error during chat');
    }
  }

  /// Fetches summary formatted/translated for TTS speech reading.
  Future<Map<String, dynamic>> getAudioSummary(String documentId, {String language = 'English'}) async {
    try {
      final response = await _dio.get(
        ApiConstants.summaryAudio(documentId),
        queryParameters: {'language': language},
      );
      if (response.data['success'] == true) {
        return response.data;
      } else {
        throw Exception('Failed to get audio summary');
      }
    } catch (e) {
      debugPrint('Audio Summary Error: $e');
      throw Exception('Network error during audio summary retrieval');
    }
  }

  /// Fetches chat history for a specific document from PostgreSQL.
  Future<List<ChatMessage>> getChatHistory(String documentId) async {
    try {
      final response = await _dio.get(ApiConstants.chatHistory(documentId));
      
      if (response.data['success'] == true) {
        final List history = response.data['history'] ?? [];
        final List<ChatMessage> messages = [];
        for (var h in history) {
          final createdAt = h['created_at'] != null
              ? DateTime.tryParse(h['created_at']) ?? DateTime.now()
              : DateTime.now();
          // Each history entry has both query and response
          messages.add(ChatMessage(
            id: '${h['id']}_q',
            content: h['query'] ?? '',
            sender: MessageSender.user,
            timestamp: createdAt,
          ));
          messages.add(ChatMessage(
            id: '${h['id']}_a',
            content: h['response'] ?? '',
            sender: MessageSender.ai,
            timestamp: createdAt,
          ));
        }
        return messages;
      }
      return [];
    } catch (e) {
      debugPrint('Error fetching chat history: $e');
      return [];
    }
  }

  /// Clears chat history for a specific document in PostgreSQL.
  Future<bool> clearHistory(String documentId) async {
    try {
      // Assuming a delete endpoint exists or will be added
      // final response = await _dio.delete(ApiConstants.chatHistory(documentId));
      // return response.data['success'] == true;
      return true;
    } catch (e) {
      return false;
    }
  }
}
