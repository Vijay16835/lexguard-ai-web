import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:lexguard_ai/features/auth/screens/forgot_password_screen.dart';
import 'package:lexguard_ai/features/auth/providers/auth_provider.dart';
import 'package:lexguard_ai/features/auth/screens/signup_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class MockAuthProvider extends AuthProvider {
  bool sendResetOtpResult = true;
  String? mockErrorMessage;
  String? lastCheckedEmail;
  bool sendResetOtpCalled = false;

  @override
  String? get errorMessage => mockErrorMessage;

  @override
  Future<bool> sendResetOtp(String email) async {
    sendResetOtpCalled = true;
    lastCheckedEmail = email;
    return sendResetOtpResult;
  }
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('ForgotPasswordScreen Flow - Registered Email', (WidgetTester tester) async {
    final mockAuth = MockAuthProvider();
    mockAuth.sendResetOtpResult = true;

    await tester.pumpWidget(
      ChangeNotifierProvider<AuthProvider>.value(
        value: mockAuth,
        child: MaterialApp(
          theme: ThemeData(useMaterial3: false),
          routes: {
            '/signup': (context) => const SignupScreen(),
            '/otp-verification': (context) => const Scaffold(body: Text('OtpVerificationScreen')),
          },
          home: const ForgotPasswordScreen(),
        ),
      ),
    );

    // Find the text field and enter a registered email
    final emailField = find.byType(TextField);
    expect(emailField, findsOneWidget);
    await tester.enterText(emailField, 'user@example.com');
    await tester.pumpAndSettle();

    // Find and tap the Send OTP button
    final sendButton = find.widgetWithText(ElevatedButton, 'Send OTP');
    expect(sendButton, findsOneWidget);
    await tester.tap(sendButton);
    await tester.pump();

    // Verify it called sendResetOtp with the email
    expect(mockAuth.sendResetOtpCalled, isTrue);
    expect(mockAuth.lastCheckedEmail, 'user@example.com');

    // Settle navigator animations and verify navigation occurred
    await tester.pumpAndSettle();
    expect(find.text('OtpVerificationScreen'), findsOneWidget);
  });

  testWidgets('ForgotPasswordScreen Flow - Unregistered Email', (WidgetTester tester) async {
    final mockAuth = MockAuthProvider();
    mockAuth.sendResetOtpResult = false;
    mockAuth.mockErrorMessage = 'Email is not registered.';

    await tester.pumpWidget(
      ChangeNotifierProvider<AuthProvider>.value(
        value: mockAuth,
        child: MaterialApp(
          theme: ThemeData(useMaterial3: false),
          routes: {
            '/signup': (context) => const SignupScreen(),
            '/otp-verification': (context) => const Scaffold(body: Text('OtpVerificationScreen')),
          },
          home: const ForgotPasswordScreen(),
        ),
      ),
    );

    // Find text field and enter an unregistered email
    final emailField = find.byType(TextField);
    await tester.enterText(emailField, 'unregistered@example.com');
    await tester.pumpAndSettle();

    // Tap Send OTP
    final sendButton = find.widgetWithText(ElevatedButton, 'Send OTP');
    await tester.tap(sendButton);
    await tester.pump();

    // Verify sendResetOtp called
    expect(mockAuth.sendResetOtpCalled, isTrue);
    expect(mockAuth.lastCheckedEmail, 'unregistered@example.com');

    // Settle to see the state change in UI
    await tester.pumpAndSettle();

    // Verify error panel and snackbar with unregistered message are displayed
    expect(find.text('Email is not registered.'), findsNWidgets(2));
    
    // Verify actions: Create Account and Back to Login
    expect(find.widgetWithText(ElevatedButton, 'Create Account'), findsOneWidget);
    expect(find.widgetWithText(OutlinedButton, 'Back to Login'), findsOneWidget);
  });
}
