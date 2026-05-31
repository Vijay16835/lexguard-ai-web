import 'package:flutter/material.dart';

/// Supported UI languages for AI responses and summaries.
/// Extend this list when adding more languages.
const List<String> kSupportedLanguages = [
  'English',
  'Tamil',
  'Hindi',
  'Telugu',
];

/// Language-to-locale-code map used by TtsService.
const Map<String, String> kLanguageLocales = {
  'English': 'en-US',
  'Tamil': 'ta-IN',
  'Hindi': 'hi-IN',
  'Telugu': 'te-IN',
};

/// Flag emoji per language for compact display in the UI.
const Map<String, String> kLanguageFlags = {
  'English': '🇺🇸',
  'Tamil': '🇮🇳',
  'Hindi': '🇮🇳',
  'Telugu': '🇮🇳',
};

/// Shared language preference that both ChatScreen and SummaryScreen observe.
/// Changing language here automatically propagates to both screens.
class LanguageProvider extends ChangeNotifier {
  String _selectedLanguage = 'English';

  String get selectedLanguage => _selectedLanguage;

  String get selectedFlag => kLanguageFlags[_selectedLanguage] ?? '🌐';

  String get selectedLocale => kLanguageLocales[_selectedLanguage] ?? 'en-US';

  void setLanguage(String lang) {
    if (lang == _selectedLanguage) return;
    if (!kSupportedLanguages.contains(lang)) return;
    _selectedLanguage = lang;
    notifyListeners();
  }
}
