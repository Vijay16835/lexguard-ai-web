import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/features/auth/screens/signup_screen.dart';
import 'package:lexguard_ai/features/auth/providers/auth_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class MockSignupAuthProvider extends AuthProvider {
  bool signUpCalled = false;
  String? lastDob;
  String? mockErrorMessage;
  bool signUpResult = true;

  @override
  String? get errorMessage => mockErrorMessage;

  @override
  Future<bool> signUp(String name, String email, String password, String dateOfBirth) async {
    signUpCalled = true;
    lastDob = dateOfBirth;
    return signUpResult;
  }
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('SignupScreen has Date of Birth Field', (WidgetTester tester) async {
    final mockAuth = MockSignupAuthProvider();

    await tester.pumpWidget(
      ChangeNotifierProvider<AuthProvider>.value(
        value: mockAuth,
        child: const MaterialApp(
          home: Scaffold(
            body: SignupScreen(),
          ),
        ),
      ),
    );

    // Let the animations run and settle
    await tester.pumpAndSettle();

    // Verify Date of Birth label is present
    expect(find.text('Date of Birth'), findsOneWidget);
  });
}
