import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';

enum TtsState { playing, stopped, paused }

class TtsService extends ChangeNotifier {
  final FlutterTts _flutterTts = FlutterTts();
  TtsState _state = TtsState.stopped;
  double _speechRate = 0.5;

  // Stored for resume support
  String _lastText = '';
  String _lastLocale = 'en-US';

  TtsState get state => _state;
  double get speechRate => _speechRate;
  bool get isPlaying => _state == TtsState.playing;
  bool get isPaused => _state == TtsState.paused;
  bool get isStopped => _state == TtsState.stopped;
  String get lastText => _lastText;

  TtsService() {
    _initTts();
  }

  void _initTts() {
    _flutterTts.setStartHandler(() {
      _state = TtsState.playing;
      notifyListeners();
    });

    _flutterTts.setCompletionHandler(() {
      _state = TtsState.stopped;
      notifyListeners();
    });

    _flutterTts.setCancelHandler(() {
      _state = TtsState.stopped;
      notifyListeners();
    });

    _flutterTts.setPauseHandler(() {
      _state = TtsState.paused;
      notifyListeners();
    });

    _flutterTts.setContinueHandler(() {
      _state = TtsState.playing;
      notifyListeners();
    });

    _flutterTts.setErrorHandler((msg) {
      _state = TtsState.stopped;
      notifyListeners();
    });

    // Default configuration
    _flutterTts.setSpeechRate(_speechRate);
    _flutterTts.setVolume(1.0);
    _flutterTts.setPitch(1.0);
  }

  Future<void> speak(String text, {String? languageCode}) async {
    if (text.trim().isEmpty) return;

    // Map language display names to locale codes if needed
    final locale = _mapLanguageToLocale(languageCode ?? 'english');
    _lastLocale = locale;
    _lastText = text;

    await _flutterTts.setLanguage(locale);
    await _flutterTts.setSpeechRate(_speechRate);
    var result = await _flutterTts.speak(text);
    if (result == 1) {
      _state = TtsState.playing;
      notifyListeners();
    }
  }

  /// Resume after pause — re-speaks stored text from the beginning on
  /// platforms that don't support native resume (iOS). On Android the
  /// platform continuation handler fires automatically.
  Future<void> resume() async {
    if (_lastText.isEmpty) return;
    await _flutterTts.setLanguage(_lastLocale);
    await _flutterTts.setSpeechRate(_speechRate);
    var result = await _flutterTts.speak(_lastText);
    if (result == 1) {
      _state = TtsState.playing;
      notifyListeners();
    }
  }

  Future<void> pause() async {
    var result = await _flutterTts.pause();
    if (result == 1) {
      _state = TtsState.paused;
      notifyListeners();
    }
  }

  Future<void> stop() async {
    var result = await _flutterTts.stop();
    if (result == 1) {
      _state = TtsState.stopped;
      notifyListeners();
    }
  }

  Future<void> setRate(double rate) async {
    _speechRate = rate;
    await _flutterTts.setSpeechRate(rate);
    notifyListeners();
  }

  String _mapLanguageToLocale(String language) {
    switch (language.toLowerCase()) {
      case 'tamil': return 'ta-IN';
      case 'hindi': return 'hi-IN';
      case 'telugu': return 'te-IN';
      case 'malayalam': return 'ml-IN';
      case 'kannada': return 'kn-IN';
      case 'french': return 'fr-FR';
      case 'spanish': return 'es-ES';
      case 'german': return 'de-DE';
      case 'arabic': return 'ar-AE';
      case 'english':
      default:
        return 'en-US';
    }
  }

  @override
  void dispose() {
    _flutterTts.stop();
    super.dispose();
  }
}
