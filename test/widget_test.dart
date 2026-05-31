import 'package:flutter_test/flutter_test.dart';
import 'package:lexguard_ai/main.dart';

void main() {
  testWidgets('LexGuard AI smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const LexGuardApp());
    expect(find.byType(LexGuardApp), findsOneWidget);
  });
}
