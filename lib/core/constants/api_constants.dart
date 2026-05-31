import 'package:flutter/foundation.dart';
import 'package:lexguard_ai/core/config/app_config.dart';

class ApiConstants {
  static const bool useMockData = false; // Set to true to run without backend
  
  static String get baseUrl {
    final url = AppConfig.apiBaseUrl;
    debugPrint('ApiConstants.baseUrl -> $url');
    return url;
  }
  
  static String get authPrefix => "/auth";
  
  // Auth Endpoints
  static String get login => "$baseUrl/auth/login";
  static String get signup => "$baseUrl/auth/signup";
  static String get googleAuth => "$baseUrl/auth/google-auth";
  static String get sendOtp => "$baseUrl/auth/send-otp";
  static String get verifyOtp => "$baseUrl/auth/verify-otp";
  static String get sendResetOtp => "$baseUrl/auth/send-reset-otp";
  static String get verifyResetOtp => "$baseUrl/auth/verify-reset-otp";
  static String get resetPassword => "$baseUrl/auth/reset-password";
  static String get health => "$baseUrl/auth/health";
  static String get logout => "$baseUrl/auth/logout";
  static String get refreshToken => "$baseUrl/auth/refresh-token";
  static String get changePassword => "$baseUrl/auth/change-password";
  static String get me => "$baseUrl/user/me";
  
  // Document Endpoints
  static String get documents => "$baseUrl/documents";
  static String get uploadDocument => "$baseUrl/documents/upload";
  static String get documentHistory => "$baseUrl/documents/history";
  static String documentDetail(String id) => "$baseUrl/documents/$id";
  static String documentStatus(String id) => "$baseUrl/documents/$id/status";
  static String documentDownload(String id) => "$baseUrl/documents/$id/download";
  static String exportReport(String id, [String format = 'pdf']) => "$baseUrl/documents/$id/export?format=$format";
  
  // AI Endpoints
  static String analyzeDocument(String id) => "$baseUrl/ai/analyze/$id";
  static String documentSummary(String id) => "$baseUrl/ai/summary/$id";
  static String riskAnalysis(String id) => "$baseUrl/ai/risk-analysis/$id";
  static String extractClauses(String id) => "$baseUrl/ai/clauses/$id";
  static String get aiChat => "$baseUrl/chat/document";
  static String chatHistory(String docId) => "$baseUrl/chat/history/$docId";
  
  // Multilingual & Voice Endpoints
  static String get multilingualChat => "$baseUrl/multilingual/chat/multilingual";
  static String get voiceChat => "$baseUrl/multilingual/chat/voice";
  static String summaryAudio(String docId) => "$baseUrl/multilingual/summary/audio/$docId";
  static String get translate => "$baseUrl/multilingual/translate";
  static String get detectLanguage => "$baseUrl/multilingual/detect-language";
}
