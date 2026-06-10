import 'package:flutter_test/flutter_test.dart';
import 'package:lexguard_ai/main.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
    FlutterSecureStorage.setMockInitialValues({});
  });

  testWidgets('LexGuard AI smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const LexGuardApp());
    expect(find.byType(LexGuardApp), findsOneWidget);
    
    // Pump past the 600ms delay in splash screen
    await tester.pump(const Duration(milliseconds: 800));
    await tester.pumpAndSettle();
  });
}


