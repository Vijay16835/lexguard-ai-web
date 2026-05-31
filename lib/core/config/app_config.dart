import 'package:flutter/foundation.dart';

enum AppFlavor { development, staging, production }

class AppConfig {
  static const String flavor = String.fromEnvironment('FLAVOR', defaultValue: 'development');
  // Android Emulator → 10.0.2.2 (reaches host machine localhost)
  // Real device on same WiFi → use your machine's LAN IP (e.g. 192.168.x.x)
  static const String apiHost = String.fromEnvironment('API_HOST', defaultValue: '10.0.2.2');
  static const String prodApiHost = String.fromEnvironment('PROD_API_HOST', defaultValue: 'api.lexguard.ai');

  static AppFlavor get environment {
    switch (flavor.toLowerCase()) {
      case 'production':
        return AppFlavor.production;
      case 'staging':
        return AppFlavor.staging;
      default:
        return AppFlavor.development;
    }
  }

  static bool get isProduction => environment == AppFlavor.production;

  static String get apiBaseUrl {
    if (kIsWeb) {
      return 'http://localhost:8001/api/v1';
    }

    switch (environment) {
      case AppFlavor.production:
        return 'https://$prodApiHost/api/v1';
      case AppFlavor.staging:
        return 'https://$apiHost/api/v1';
      case AppFlavor.development:
      default:
        return 'http://$apiHost:8001/api/v1';
    }
  }
}