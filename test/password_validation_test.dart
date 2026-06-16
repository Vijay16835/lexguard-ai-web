import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Password Strong Validation Regex Tests', () {
    final regex = RegExp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$');

    test('Valid Passwords', () {
      expect(regex.hasMatch('Password123!'), isTrue);
      expect(regex.hasMatch('LexGuard@2026'), isTrue);
    });

    test('Invalid Passwords - No Uppercase', () {
      expect(regex.hasMatch('password123!'), isFalse);
    });

    test('Invalid Passwords - No Lowercase', () {
      expect(regex.hasMatch('PASSWORD123!'), isFalse);
    });

    test('Invalid Passwords - No Number', () {
      expect(regex.hasMatch('Password!!!'), isFalse);
    });

    test('Invalid Passwords - Too Short', () {
      expect(regex.hasMatch('Pass12!'), isFalse);
    });

    test('Invalid Passwords - Disallowed Special Character', () {
      expect(regex.hasMatch('Password123#'), isFalse);
    });
  });
}
