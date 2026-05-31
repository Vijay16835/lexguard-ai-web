import 'package:lexguard_ai/core/constants/api_constants.dart';

class AppConstants {
  // App Info
  static const String appName = 'LexGuard AI';
  static const String appVersion = '1.0.0';
  static const String appTagline = 'Intelligent Legal Document Analyzer';

  // API Endpoints
  static String get baseUrl => ApiConstants.baseUrl;
  static String get analyzeEndpoint => '${ApiConstants.baseUrl}/ai/analyze';
  static String get chatEndpoint => ApiConstants.aiChat;
  static String get summaryEndpoint => '${ApiConstants.baseUrl}/ai/summary';

  // Storage Keys
  static const String tokenKey = 'auth_token';
  static const String userKey = 'user_data';
  static const String themeKey = 'app_theme';
  static const String onboardingKey = 'onboarding_done';

  // File Types
  static const List<String> supportedFileTypes = ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png'];
  static const int maxFileSizeMB = 50;

  // AI Model
  static const String aiModel = 'LexGuard-Legal-v2';
  static const double aiAccuracy = 94.7;

  // Subscription Plans
  static const String freePlan = 'Free';
  static const String proPlan = 'Pro';
  static const String enterprisePlan = 'Enterprise';

  // Dummy User
  static const String dummyUserName = 'Alex Johnson';
  static const String dummyUserEmail = 'alex.johnson@lawfirm.com';
  static const String dummyUserRole = 'Senior Attorney';
  static const String dummyUserPlan = 'Pro';
  static const int dummyDocsAnalyzed = 247;
}
